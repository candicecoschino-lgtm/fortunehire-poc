import sys,json,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import collect_jobs as c
from home_depot_public import discover,search_data
HOST='careers.homedepot.com';URL='https://'+HOST+'/job/12345/synthetic-role/'
def job(url=URL):
 d={'@type':'JobPosting','title':'Synthetic store associate','identifier':{'value':'SHARED-REF'},'datePosted':'2026-11-14','url':url,'description':'Role duties.','jobLocation':{'address':{'addressCountry':'US','addressRegion':'UT','addressLocality':'Test City'}}}
 return '<script type="application/ld+json">'+json.dumps(d)+'</script><aside>Work Type: Remote</aside>'
class HomeDepotTests(unittest.TestCase):
 def test_matching_current_job_supplies_schedule_without_using_unrelated_page_text(self):
  from home_depot_public import enrich
  source={'identifier':{'value':'SHARED-REF'},'url':URL,'description':'Role duties.'}
  record={'id':12345,'ref':'SHARED-REF','scout_orgid':1814,'employment_type':'Full_time'}
  html=lambda row:'<script>var current_job = '+json.dumps(row)+';</script>'
  self.assertEqual(enrich(source,html(record))['employmentType'],'Full_time')
  self.assertEqual(enrich({k:v for k,v in source.items() if k!='url'},html(record),URL)['employmentType'],'Full_time')
  for invalid in [{**record,'id':99999},{**record,'ref':'OTHER'},{**record,'scout_orgid':999}]:
   self.assertNotIn('employmentType',enrich(source,html(invalid)))
  self.assertNotIn('employmentType',enrich(source,html(record)+html(record)))
 def test_discovery_requires_employer_org_us_country_and_matching_individual_id(self):
  client=Mock(host=HOST);api=Mock();row={'id':12345,'url':URL,'scout_orgid':1814,'primary_country':'US','open_date':'2026-11-14T10:00:00','timestamp':'2099-01-01'}
  data={'totalHits':200,'searchResults':[{'job':row},{'job':{**row,'scout_orgid':999}},{'job':{**row,'primary_country':'CA'}},{'job':{**row,'url':URL.replace(HOST,'other.example')}}]}
  api.get.return_value=(200,'CWS.jobs.jobCallback('+json.dumps(data)+');');self.assertEqual(discover(client,Mock(return_value=api)),{'12345':URL});self.assertEqual(client.discovery_dates,{'12345':'2026-11-14'})
 def test_jsonp_is_decoded_as_data_and_rejects_trailing_code(self):
  for body in ['OtherCallback({"searchResults":[]})','CWS.jobs.jobCallback({"searchResults":[]});alert(1)','CWS.jobs.jobCallback({"error":"bad"})']:
   with self.assertRaises(ValueError):search_data(body)
 def test_reused_requisition_has_distinct_public_posting_ids_and_navigation_cannot_set_work_model(self):
  with patch.dict(c.SOURCES,{'home-depot':(HOST,'Retail')}):
   a=c.normalize_posting(job(),URL,'home-depot',datetime(2026,11,15,tzinfo=timezone.utc));other=URL.replace('12345','54321');b=c.normalize_posting(job(other),other,'home-depot',datetime(2026,11,15,tzinfo=timezone.utc))
   self.assertNotEqual(a['id'],b['id']);self.assertEqual(a['identifierType'],'posting-id');self.assertIn('SHARED-REF',a['sourceNote']);self.assertEqual(a['arrangement'],'unknown')

 def test_role_sections_preserve_pay_and_remote_caveat_without_inventing_period_or_states(self):
  from home_depot_public import enrich
  source={'@type':'JobPosting','title':'Synthetic engineer (Remote)','identifier':{'value':'R1'},'datePosted':'2026-11-14','url':URL,'description':'No travel required.','jobLocationType':'TELECOMMUTE','applicantLocationRequirements':{'@type':'Country','name':'US'},'jobLocation':{'address':{'addressCountry':'US','addressRegion':'GA','addressLocality':'Atlanta'}}}
  sections='<span id="gtm-jobdetail-idSC">R1</span><div><div id="payrange"></div><div class="fusion-builder-row-inner"><h2>Pay Range</h2><p>The pay range for this position is between $80,000 – $180,000.</p></div><div id="worklocation"></div><div class="fusion-builder-row-inner"><h2>Work Location</h2><p>Remote/virtual – Depending on the position, a remote role may require living within a commutable distance of an assigned company office.</p></div></div><aside>Work Type: Hybrid. Salary $900,000 per year.</aside>'
  body='<script type="application/ld+json">'+json.dumps(source)+'</script>'+sections
  with patch.dict(c.SOURCES,{'home-depot':(HOST,'Retail')}):
   j=c.normalize_posting(body,URL,'home-depot',datetime(2026,11,15,tzinfo=timezone.utc))
  self.assertEqual(j['arrangement'],'remote');self.assertEqual(j['remoteScope'],'unknown');self.assertEqual(j['eligibleStates'],[]);self.assertIsNone(j['salary']);self.assertIn('80,000',j['publishedPay']['text']);self.assertNotIn('900,000',j['publishedPay']['text']);self.assertIn('commutable',j['sourceNote']);self.assertFalse(j['travelRequired'])
  with self.assertRaisesRegex(ValueError,'requisition'):enrich(source,sections.replace('>R1<','>OTHER<'))

 def test_only_matching_anchored_section_controls_work_location(self):
  from home_depot_public import enrich
  source={'identifier':{'value':'R1'},'description':'Role duties.'}
  body='<span id="gtm-jobdetail-idSC">R1</span><div><div id="worklocation"></div><div class="fusion-builder-row-inner"><h2>Work Location</h2><p>Onsite – This job works at the store.</p></div></div>'
  self.assertEqual(enrich(source,body)['jobLocationType'],'ON_SITE')
  self.assertNotIn('jobLocationType',enrich(source,body.replace('<h2>Work Location</h2>','<h2>Similar Roles</h2>')))
