"""Synthetic fixtures for verified public Oracle and Verizon formats."""
import sys,json,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from unittest.mock import Mock,patch
from datetime import datetime,timezone
import collect_jobs as c
from employer_sources import public_search,public_fetch,ORACLE
from employer_adapters import oracle
NOW=datetime(2026,11,14,2,tzinfo=timezone.utc)
DELL='https://enterpriseplatform.dell.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/123'
VERIZON='https://mycareer.verizon.com/jobs/r-test/test-role/'

def oracle_data(**changes):
    source={'Id':'123','Title':'Synthetic engineer','ExternalPostedStartDate':'2026-11-14T00:37:26+00:00','ExternalDescriptionStr':'<p>Role description.</p>','ExternalQualificationsStr':'<p>Skills.</p>','InternalQualificationsStr':'Internal text must not be published #LI-Remote','JobSchedule':'Part time','WorkplaceTypeCode':'ORA_ON_SITE','workLocation':[{'TownOrCity':'Test City','Country':'US','Region1':'Washington','Region2':'OR'}]}
    source.update(changes);return json.dumps({'items':[source]})

def verizon_data(**changes):
    source={'Id':'r-test','Reference':'R-TEST','Title':'Synthetic advisor','DisplayDate':'2026-11-12T08:00:00Z','UpdateDate':'2026-11-14T08:00:00Z','Urls':[{'Url':'/jobs/r-test/test-role/'}],'Locations':[{'City':'Test City','Region':'CA','Country':'United States of America'}]}
    source.update(changes)
    stream='1:'+json.dumps({'job':json.dumps(source)})+'\n'
    # The stream may split in the middle of a record or an escaped string.
    halves=[stream[:37],stream[37:]]
    scripts=''.join('<script>self.__next_f.push('+json.dumps([1,part])+')</script>' for part in halves)
    return scripts+'<div data-testid="job-page" data-job-id="r-test"><div class="wysiwyg"><p>This is a hybrid position.</p></div></div><aside><p>Work Type: Remote</p></aside>'

class EmployerSourceTests(unittest.TestCase):
    def test_walmart_soft404_requires_exact_employer_template_without_active_payload(self):
        client=Mock(host='careers.walmart.com')
        missing='<main id="main-content"><div>404</div><div>Sorry, but it looks like this page no longer exists.</div></main>'
        client.get.return_value=(200,missing)
        self.assertEqual(public_fetch(client,'https://careers.walmart.com/us/en/jobs/R-123',Mock()),(404,''))
        for body in [missing+'<script id="__NEXT_DATA__">{}</script>',missing.replace('404','Error'),missing.replace('main-content','recommendations')]:
            client.get.return_value=(200,body)
            self.assertEqual(public_fetch(client,'https://careers.walmart.com/us/en/jobs/R-123',Mock()),(200,body))

    def test_oracle_exact_empty_lookup_uses_repeated_missing_guard_not_immediate_closure(self):
        client=Mock(host='enterpriseplatform.dell.com')
        client.oracle_data_client=None
        empty={'items':[],'count':0,'hasMore':False}
        client.get.side_effect=[(200,'<html>public page</html>'),(200,json.dumps(empty))]
        self.assertEqual(public_fetch(client,DELL,Mock()),(404,''))
        self.assertIn('ById',client.get.call_args.args[0])
        for changed in [dict(empty,error='service failure'),dict(empty,hasMore=True),{'items':[]}]:
            payload=json.dumps(changed);client.get.side_effect=[(200,'<html></html>'),(200,payload)]
            self.assertEqual(public_fetch(client,DELL,Mock()),(200,payload))

    def test_workday_outage_redirect_is_identified_without_following_other_hosts(self):
        redirect=c.RestrictedRedirect('coke.wd1.myworkdayjobs.com')
        req=c.urllib.request.Request('https://coke.wd1.myworkdayjobs.com/sitemap.xml')
        with self.assertRaisesRegex(c.SourceError,'Workday outage redirect'):
            redirect.redirect_request(req,None,302,'Found',{},'https://www.myworkday.com/wday/drs/outage?t=coke&s=sitemap.xml')
        for target in ['https://www.myworkday.com/wday/drs/outage?t=another','https://www.myworkday.com.evil.example/wday/drs/outage?t=coke','https://www.myworkday.com:8443/wday/drs/outage?t=coke','http://www.myworkday.com/wday/drs/outage?t=coke']:
            with self.assertRaises(ValueError):redirect.redirect_request(req,None,302,'Found',{},target)

    def test_oracle_public_details_keep_date_identity_state_and_scope(self):
        with patch.dict(c.SOURCES,{'dell':('enterpriseplatform.dell.com','Technology')}):
            j=c.normalize_posting(oracle_data(),DELL,'dell',NOW)
            self.assertEqual(j['postedAt'],'2026-11-13')
            self.assertTrue(c.recent_posting(j,NOW))
            self.assertEqual(j['arrangement'],'on-site')
            self.assertEqual(j['employmentType'],'Part-time')
            self.assertEqual(j['locations'],[{'city':'Test City','state':'Oregon'}])
            self.assertEqual(j['collectionMethod'],'oracle-public-requisition-details')
            self.assertEqual(j['eligibleStates'],[])
            self.assertEqual(c.normalize_posting(oracle_data(WorkplaceTypeCode=None,WorkplaceType=None),DELL,'dell',NOW)['arrangement'],'unknown')

    def test_oracle_rejects_mismatched_ambiguous_and_undated_details(self):
        self.assertIsNone(oracle(oracle_data(Id='OTHER'),DELL))
        self.assertIsNone(oracle(oracle_data(ExternalPostedStartDate=None),DELL))
        data=json.loads(oracle_data());data['items']*=2
        self.assertIsNone(oracle(json.dumps(data),DELL))
        self.assertIsNone(oracle(oracle_data(ExternalPostedStartDate='2026-11-13T12:00:00'),DELL))

    def test_oracle_search_is_bounded_scoped_and_filters_foreign_rows(self):
        client=Mock(host='enterpriseplatform.dell.com')
        def result(url):
            return 200,json.dumps({'items':[{'SiteNumber':'CX_1001','TotalJobsCount':200,'requisitionList':[{'Id':str(i),'PrimaryLocationCountry':'DE','PostedDate':'2026-11-13'} for i in range(19)]+[{'Id':'US-'+str(client.get.call_count),'PrimaryLocationCountry':'US','PostedDate':'2026-11-13'}]}]})
        client.get.side_effect=result
        found=public_search(client,Mock())
        self.assertEqual(len(found),3);self.assertEqual(client.get.call_count,3)
        self.assertTrue(client.discovery_limited)
        self.assertTrue(all('/en/sites/CX_1001/job/US-' in u for u in found.values()))

    def test_oracle_search_uses_only_reviewed_backend_and_career_site(self):
        client=Mock(host='www.krogerfamilycareers.com');backend=Mock()
        backend.get.return_value=(200,json.dumps({'items':[{'SiteNumber':'WRONG','requisitionList':[]}]}))
        factory=Mock(return_value=backend)
        with self.assertRaises(ValueError):public_search(client,factory)
        factory.assert_called_once_with('eluq.fa.us2.oraclecloud.com')
        client.get.assert_not_called()
        self.assertIsNone(public_search(Mock(host='unreviewed.example'),factory))

    def test_oracle_fetch_checks_application_page_and_preserves_access_failures(self):
        client=Mock(host='enterpriseplatform.dell.com');client.get.side_effect=[(410,''),(200,'page'),(200,oracle_data())]
        self.assertEqual(public_fetch(client,DELL,Mock()),(410,''))
        client.oracle_data_client=client
        self.assertEqual(public_fetch(client,DELL,Mock())[1],oracle_data())
        self.assertIn('ById',client.get.call_args.args[0])
        client.get.side_effect=c.SourceError('HTTP 403')
        with self.assertRaises(c.SourceError):public_fetch(client,DELL,Mock())

    def test_verizon_uses_posted_date_not_update_or_footer(self):
        with patch.dict(c.SOURCES,{'verizon':('mycareer.verizon.com','Communication Services')}):
            j=c.normalize_posting(verizon_data(),VERIZON,'verizon',NOW)
            self.assertEqual(j['postedAt'],'2026-11-12')
            self.assertEqual(j['arrangement'],'hybrid')
            self.assertEqual(j['locations'],[{'city':'Test City','state':'California'}])
            old=c.normalize_posting(verizon_data(DisplayDate='2026-10-09T07:00:00Z'),VERIZON,'verizon',NOW)
            self.assertFalse(c.recent_posting(old,NOW))
            with self.assertRaises(ValueError):c.normalize_posting(verizon_data(Urls=[{'Url':'/jobs/r-other/role/'}]),VERIZON,'verizon',NOW)

    def test_humana_annual_base_pay_is_scoped_and_mixed_visit_pay_stays_text(self):
        loc=[{'city':'Test City','state':'Florida'}]
        description='The compensation range below reflects a good faith estimate of starting base pay for full time employment.\n$37,440 - $42,500 per year'
        salary,pay=c.extract_published_pay(description,loc,'humana')
        self.assertEqual(salary['period'],'year');self.assertEqual(salary['scopeStates'],['Florida'])
        salary,pay=c.extract_published_pay('Pay Per Visit/Unit Rate $49.00 - $69.00\n'+description,loc,'humana')
        self.assertIsNone(salary);self.assertIn('Visit',pay['text'])
        salary,pay=c.extract_published_pay('The annual salary range for the location(s) listed on this job requisition is: $37,000.00 - $64,000.00.',loc,'verizon')
        self.assertEqual(salary['period'],'year')

    def test_verizon_role_work_model_is_not_mobile_work_or_company_policy(self):
        with patch.dict(c.SOURCES,{'verizon':('mycareer.verizon.com','Communication Services')}):
            for sentence,expected in [("In this remote role, you'll work from home.",'remote'),("In this hybrid role, you'll have a defined work location.",'hybrid'),("In this worksite-based role, you'll work onsite at a defined location(s).",'on-site'),("In this mobile role, you'll primarily work from customer locations.",'unknown')]:
                body=verizon_data().replace('This is a hybrid position.',sentence)
                self.assertEqual(c.normalize_posting(body,VERIZON,'verizon',NOW)['arrangement'],expected)

if __name__=='__main__':unittest.main()
