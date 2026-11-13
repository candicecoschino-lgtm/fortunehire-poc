"""Synthetic lifecycle fixtures: never published as real jobs."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import copy
import json
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, MagicMock, patch
import collect_jobs as c

NOW=datetime(2026,11,13,15,tzinfo=timezone.utc)
URL='https://jobs.boeing.com/job/test-city/test-engineer/185/12345'


def body(**changes):
    j={'@type':'JobPosting','title':'Synthetic lifecycle test','identifier':{'value':'TEST-1'},'url':URL,'datePosted':'2026-11-12','description':'<p>This position is expected to be 100% onsite.</p>','jobLocation':[{'address':{'addressCountry':'US','addressRegion':'FL','addressLocality':'Test City'}}]}
    j.update(changes)
    return '<script type="application/ld+json">'+json.dumps(j)+'</script>'


class CollectorTests(unittest.TestCase):
    def client_without_network(self):
        client=c.Client.__new__(c.Client)
        client.host='jobs.boeing.com';client.delay=0;client.last=0
        client.robots=c.urllib.robotparser.RobotFileParser();client.robots.parse([])
        client.opener=Mock()
        return client

    def test_interrupted_download_retries_then_succeeds(self):
        client=self.client_without_network()
        response=MagicMock();response.__enter__.return_value.status=200
        response.__enter__.return_value.read.return_value=b'complete response'
        client.opener.open.side_effect=[c.http.client.IncompleteRead(b'partial'),response]
        with patch('collect_jobs.time.sleep'):
            self.assertEqual(client.get(URL),(200,'complete response'))
        self.assertEqual(client.opener.open.call_count,2)

    def test_retry_limit_and_access_denials(self):
        client=self.client_without_network()
        client.opener.open.side_effect=c.http.client.IncompleteRead(b'partial')
        with patch('collect_jobs.time.sleep'),self.assertRaises(c.SourceError): client.get(URL)
        self.assertEqual(client.opener.open.call_count,3)
        client=self.client_without_network()
        client.opener.open.side_effect=c.urllib.error.HTTPError(URL,403,'Denied',{},None)
        with patch('collect_jobs.time.sleep'),self.assertRaises(c.SourceError): client.get(URL)
        self.assertEqual(client.opener.open.call_count,1)

    def test_initial_import(self):
        jobs,state,r=c.reconcile('boeing',[],{}, {'12345':URL},lambda u:(200,body()),NOW)
        self.assertEqual(r['added'],1)
        self.assertEqual(jobs[0]['arrangement'],'on-site')
        self.assertEqual(jobs[0]['locations'][0]['state'],'Florida')

    def test_changed_title_updates_in_place_and_no_duplicates_on_repeat(self):
        old=c.normalize_posting(body(),URL,'boeing',NOW)
        out,state,r=c.reconcile('boeing',[old],{}, {'12345':URL},lambda u:(200,body(title='Changed synthetic title')),NOW)
        self.assertEqual(len(out),1);self.assertEqual(r['changed'],1)
        self.assertEqual(out[0]['title'],'Changed synthetic title')
        out,state,r=c.reconcile('boeing',out,state,{'12345':URL},lambda u:(200,body(title='Changed synthetic title')),NOW)
        self.assertEqual(len(out),1);self.assertEqual(r['added'],0);self.assertEqual(r['changed'],0)

    def test_absence_from_discovery_still_checks_existing_url(self):
        old=c.normalize_posting(body(),URL,'boeing',NOW)
        fetch=Mock(return_value=(200,body()))
        out,state,r=c.reconcile('boeing',[old],{}, {},fetch,NOW)
        fetch.assert_called_once_with(URL);self.assertEqual(out[0]['status'],'reviewed')

    def test_closed_only_after_two_missing_checks_six_hours_apart(self):
        old=c.normalize_posting(body(),URL,'boeing',NOW)
        out,state,r=c.reconcile('boeing',[old],{}, {},lambda u:(404,''),NOW)
        self.assertEqual(out[0]['status'],'reviewed')
        out,state,r=c.reconcile('boeing',out,state,{},lambda u:(410,''),NOW+timedelta(hours=7))
        self.assertEqual(out[0]['status'],'closed');self.assertEqual(r['closed'],1)

    def test_explicit_soft_closed_page_needs_two_checks(self):
        old=c.normalize_posting(body(),URL,'boeing',NOW)
        fetch=lambda u:(200,'<main>Sorry, this job is no longer available.</main>')
        out,state,r=c.reconcile('boeing',[old],{}, {},fetch,NOW)
        self.assertEqual(out[0]['status'],'reviewed');self.assertFalse(r['errors'])
        self.assertEqual(r['pendingClosureChecks'],1)
        out,state,r=c.reconcile('boeing',out,state,{},fetch,NOW+timedelta(hours=7))
        self.assertEqual(out[0]['status'],'closed')

    def test_canonical_slug_change_keeps_posting_identity(self):
        canonical=URL.replace('test-engineer','renamed-engineer')
        j=c.normalize_posting(body(url=canonical),URL,'boeing',NOW)
        self.assertEqual(j['url'],canonical);self.assertEqual(j['requisitionId'],'TEST-1')

    def test_missing_signal_clears_when_job_returns(self):
        old=c.normalize_posting(body(),URL,'boeing',NOW)
        out,state,r=c.reconcile('boeing',[old],{}, {},lambda u:(404,''),NOW)
        out,state,r=c.reconcile('boeing',out,state,{},lambda u:(200,body()),NOW+timedelta(hours=7))
        self.assertFalse(state['missing']);self.assertEqual(out[0]['status'],'reviewed')

    def test_access_denial_or_bad_html_does_not_refresh_or_delete(self):
        old=c.normalize_posting(body(),URL,'boeing',NOW)
        for result in [(200,'<html>Maintenance</html>'),(503,'')]:
            out,state,r=c.reconcile('boeing',[old],{}, {},lambda u:result,NOW+timedelta(days=1))
            self.assertEqual(out,[old]);self.assertTrue(r['errors'])

    def test_new_unparseable_candidate_quarantined_without_publication(self):
        out,state,r=c.reconcile('boeing',[],{}, {'12345':URL},lambda u:(200,'<html>Unsupported format</html>'),NOW)
        self.assertFalse(out);self.assertFalse(r['errors']);self.assertTrue(r['warnings'])
        self.assertIn('12345',state['quarantined'])
        fetch=Mock(return_value=(200,body()))
        c.reconcile('boeing',[],state,{'12345':URL},fetch,NOW+timedelta(hours=1))
        fetch.assert_not_called()

    def test_citi_job_type_label_and_visible_changes_affect_hash(self):
        hybrid=c.normalize_posting(body()+'<h2>Job Type:</h2><span>Hybrid</span>',URL,'boeing',NOW)
        onsite=c.normalize_posting(body()+'<h2>Job Type:</h2><span>On-site</span>',URL,'boeing',NOW)
        self.assertEqual(hybrid['arrangement'],'hybrid');self.assertNotEqual(hybrid['sourceHash'],onsite['sourceHash'])

    def test_mass_closure_guard(self):
        jobs=[]
        for i in range(8):
            u=URL[:-5]+str(12345+i)
            jobs.append(c.normalize_posting(body(url=u,identifier={'value':'TEST-'+str(i)}),u,'boeing',NOW))
        state={'missing':{j['id']:NOW.isoformat() for j in jobs}}
        out,state,r=c.reconcile('boeing',jobs,state,{},lambda u:(404,''),NOW+timedelta(hours=7))
        self.assertTrue(all(j['status']=='reviewed' for j in out));self.assertTrue(r['errors'])

    def test_office_address_or_remote_title_does_not_invent_arrangement(self):
        j=c.normalize_posting(body(title='Remote synthetic title',description='Office benefits include hybrid options for some roles.'),URL,'boeing',NOW)
        self.assertEqual(j['arrangement'],'unknown');self.assertEqual(j['eligibleStates'],[])
        self.assertIsNone(j['salary']);self.assertIsNone(j['travelRequired'])

    def test_explicit_remote_eligibility_and_labeled_hybrid(self):
        j=c.normalize_posting(body(jobLocationType='TELECOMMUTE',applicantLocationRequirements=[{'name':'Florida'}]),URL,'boeing',NOW)
        self.assertEqual(j['remoteScope'],'states');self.assertEqual(j['eligibleStates'],['Florida'])
        j=c.normalize_posting(body()+'<p>Remote Job: Hybrid</p>',URL,'boeing',NOW)
        self.assertEqual(j['arrangement'],'hybrid');self.assertEqual(j['remoteScope'],'unknown')

    def test_wrong_host_identity_or_incomplete_data_rejected(self):
        with self.assertRaises(ValueError): c.normalize_posting(body(),URL.replace('jobs.boeing.com','evil.example'),'boeing',NOW)
        with self.assertRaises(ValueError): c.normalize_posting(body(url='https://jobs.boeing.com/job/test/other/185/456'),URL,'boeing',NOW)
        with self.assertRaises(ValueError): c.normalize_posting(body(identifier={}),URL,'boeing',NOW)
        self.assertIsNone(c.normalize_posting(body(jobLocation=[{'address':{'addressCountry':'CA','addressRegion':'ON','addressLocality':'Toronto'}}]),URL,'boeing',NOW))

    def test_explicit_deadline_closes_job(self):
        j=c.normalize_posting(body(validThrough='2026-11-12',datePosted='2026-11-10'),URL,'boeing',NOW)
        self.assertEqual(j['status'],'closed')

    def test_deadline_before_posting_is_not_a_confirmed_closure(self):
        j=c.normalize_posting(body(validThrough='2026-10-08',datePosted='2026-11-12'),URL,'boeing',NOW)
        self.assertIsNone(j['closesAt']);self.assertEqual(j['status'],'reviewed')
        self.assertIn('predates',j['evidence']['deadline'])

    def test_description_deadline_and_employer_remote_statement(self):
        j=c.normalize_posting(body(description="You'll enjoy the flexibility to work remotely * from anywhere within the U.S. Applications for this position will be accepted until Nov. 12, 2026"),URL,'boeing',NOW)
        self.assertEqual(j['arrangement'],'remote');self.assertEqual(j['remoteScope'],'nationwide')
        self.assertEqual(j['status'],'closed');self.assertEqual(j['closesAt'],'2026-11-12')

    def test_closed_job_can_reopen_on_positive_posting(self):
        old=c.normalize_posting(body(validThrough='2026-11-12'),URL,'boeing',NOW)
        out,state,r=c.reconcile('boeing',[old],{}, {'12345':URL},lambda u:(200,body()),NOW)
        self.assertEqual(len(out),1);self.assertEqual(out[0]['status'],'reviewed')

    def test_graph_and_ampersands(self):
        parsed=json.loads(c.Page(body(title='Research & Development')).scripts[0])
        wrapped='<script type="application/ld+json">'+json.dumps({'@graph':[parsed]})+'</script>'
        self.assertEqual(c.normalize_posting(wrapped,URL,'boeing',NOW)['title'],'Research & Development')

    def test_robot_rules_and_sitemap_validation(self):
        rp=c.urllib.robotparser.RobotFileParser();rp.parse(['User-agent: *','Disallow: /search-jobs/'])
        self.assertFalse(rp.can_fetch(c.UA,'https://jobs.boeing.com/search-jobs/results'))
        self.assertTrue(rp.can_fetch(c.UA,URL))
        client=Mock(host='jobs.boeing.com');client.get.return_value=(200,'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>'+URL+'</loc></url></urlset>')
        self.assertEqual(c.discover(client),{'12345':URL})
        client.get.return_value=(200,'<html>Maintenance</html>')
        with self.assertRaises(c.SourceError): c.discover(client)

    def test_no_location_pay_assumptions(self):
        base={'currency':'USD','value':{'minValue':20,'maxValue':30,'unitText':'HOUR'}}
        j=c.normalize_posting(body(baseSalary=base),URL,'boeing',NOW)
        self.assertEqual(j['salary']['scopeStates'],['Florida'])
        loc=[{'address':{'addressCountry':'US','addressRegion':'FL','addressLocality':'A'}},{'address':{'addressCountry':'US','addressRegion':'NY','addressLocality':'B'}}]
        self.assertIsNone(c.normalize_posting(body(baseSalary=base,jobLocation=loc),URL,'boeing',NOW)['salary'])

    def test_published_hourly_pay_is_extracted_and_updates(self):
        text='The hourly pay for this role will range from $18 - $32 per hour based on full-time employment.'
        j=c.normalize_posting(body(description=text),URL,'boeing',NOW)
        self.assertEqual(j['salary']['min'],18);self.assertEqual(j['salary']['period'],'hour')
        self.assertEqual(j['salary']['scopeStates'],['Florida'])
        changed=c.normalize_posting(body(description=text.replace('$18','$20')),URL,'boeing',NOW)
        self.assertEqual(changed['salary']['min'],20)
        self.assertNotEqual(j['sourceHash'],changed['sourceHash'])

    def test_hourly_unit_between_both_amounts(self):
        j=c.normalize_posting(body(description='Summary pay range $24.00/hr - $45.13/hr'),URL,'boeing',NOW)
        self.assertEqual(j['salary']['min'],24);self.assertEqual(j['salary']['max'],45.13)
        self.assertEqual(j['salary']['period'],'hour')

    def test_annual_pay_and_ambiguous_multiple_bands(self):
        text='The annual pay for this role will range from $90,000 - $120,000 per year.'
        j=c.normalize_posting(body(description=text),URL,'boeing',NOW)
        self.assertEqual(j['salary']['period'],'year');self.assertEqual(j['salary']['max'],120000)
        text='Summary pay range Level 2: $90,000 - $120,000\nSummary pay range Level 3: $110,000 - $140,000'
        # HTML paragraphs preserve independent published band labels.
        j=c.normalize_posting(body(description='<p>'+text.replace('\n','</p><p>')+'</p>'),URL,'boeing',NOW)
        self.assertIsNone(j['salary']);self.assertIn('$140,000',j['publishedPay']['text'])

    def test_citi_primary_pay_is_not_applied_to_secondary_state(self):
        locations=[{'city':'New York','state':'New York'},{'city':'Irving','state':'Texas'}]
        text='Primary Location:\nNew York New York United States\nPrimary Location Full Time Salary Range:\n$170,000.00 - $300,000.00'
        salary,published=c.extract_published_pay(text,locations,'citigroup')
        self.assertIsNone(salary);self.assertEqual(published['scopeStates'],['New York'])
        self.assertIn('$170,000.00',published['text']);self.assertIn('period',published['note'])

    def test_citi_primary_street_address_matches_listed_city(self):
        locations=[{'city':'Jersey City','state':'New Jersey'},{'city':'Tampa','state':'Florida'}]
        text='Primary Location:\n480 WASHINGTON BOULEVARD JERSEY CITY\nPrimary Location Full Time Salary Range:\n$250,000.00 - $500,000.00'
        salary,published=c.extract_published_pay(text,locations,'citigroup')
        self.assertEqual(published['scopeStates'],['New Jersey'])

    def test_reported_uhg_wording_extracts_pay_travel_and_national_remote(self):
        description="<p>You'll enjoy the flexibility to telecommute* from anywhere within the U.S.</p><p>This position is full-time (40 hours per week).</p><p>Must live in a location that can receive an approved internet connection.</p><p>The salary for this role will range from $112,700 - $193,200 annually based on full-time employment.</p>"
        j=c.normalize_posting(body(description=description)+'<div>Travel: Yes, 50 % of the Time</div>',URL,'boeing',NOW)
        self.assertEqual(j['arrangement'],'remote');self.assertEqual(j['remoteScope'],'nationwide')
        self.assertEqual(j['salary']['min'],112700);self.assertEqual(j['salary']['max'],193200)
        self.assertEqual(j['salary']['period'],'year');self.assertEqual(j['salary']['scopeStates'],[])
        self.assertTrue(j['travelRequired']);self.assertIn('50',j['travelNote'])
        self.assertEqual(j['employmentType'],'Full-time')

    def test_nationwide_phrase_with_actual_residency_restriction_stays_unknown(self):
        text="<p>You'll enjoy the flexibility to work remotely from anywhere within the U.S.</p><p>Must reside in California.</p>"
        j=c.normalize_posting(body(description=text),URL,'boeing',NOW)
        self.assertEqual(j['arrangement'],'remote');self.assertEqual(j['remoteScope'],'unknown')

    def test_posting_window_exact_boundary_and_unknown_dates(self):
        for posted,expected in [('2026-10-30',True),('2026-10-29',False),('2026-11-14',False),(None,False)]:
            self.assertEqual(c.recent_posting({'postedAt':posted},NOW),expected)

    def test_old_posting_is_not_rejuvenated_by_successful_fetch(self):
        out,state,r=c.reconcile('boeing',[],{}, {'12345':URL},lambda u:(200,body(datePosted='2026-10-23')),NOW)
        self.assertEqual(out,[]);self.assertEqual(r['outsidePostingWindow'],1);self.assertFalse(r['errors'])
        old=c.normalize_posting(body(datePosted='2026-10-23'),URL,'boeing',NOW)
        fetch=Mock(return_value=(200,body()))
        out,state,r=c.reconcile('boeing',[old],{}, {},fetch,NOW)
        self.assertEqual(out,[]);fetch.assert_not_called()


if __name__=='__main__': unittest.main()

