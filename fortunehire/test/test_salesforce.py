"""Synthetic public snapshot and posting fixtures, never published."""
import sys,json,unittest
from pathlib import Path
from datetime import datetime,timezone,timedelta
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import collect_jobs as c
from employer_sources import public_search,salesforce_rows
from salesforce_details import enrich
HOST='salesforce.wd12.myworkdayjobs.com'
URL='https://'+HOST+'/External_Career_Site/job/New-York---New-York/Synthetic-Role_JR12345'
def row(**kw):
 d={'Countries':['United States of America'],'Job_Requisition_Ref_ID':'JR12345','External_Job_Posting_Site':URL,'External_Job_Posting_Start_Date':'2026-11-12'};d.update(kw);return d
def snapshot(rows,**kw):
 d={'Count':len(rows),'Total_Jobs':len(rows),'Report_Entry':rows,'Fetch_Timestamp':(datetime.now(timezone.utc)-timedelta(minutes=1)).isoformat()};d.update(kw);return json.dumps(d)
def posting(location='New York - New York',**kw):
 j={'@type':'JobPosting','identifier':{'value':'JR12345'},'title':'Synthetic advisor','datePosted':'2026-11-12','description':'Role duties.','jobLocation':{'address':{'addressCountry':'United States of America','addressLocality':location}},'jobLocationType':'TELECOMMUTE','applicantLocationRequirements':{'@type':'Country','name':'United States of America'}};j.update(kw)
 return '<link rel="canonical" href="https://'+HOST+'/en-US/External_Career_Site/job/Synthetic-Role_JR12345-1"><script type="application/ld+json">'+json.dumps(j)+'</script>'
class SalesforceTests(unittest.TestCase):
 def test_discovery_checks_complete_recent_snapshot_country_and_exact_posting_identity(self):
  client=Mock(host=HOST);data_client=Mock();data_client.get.return_value=(200,snapshot([row(),row(Countries=['Canada'],Job_Requisition_Ref_ID='JR777'),row(External_Job_Posting_Site=URL.replace(HOST,'other.wd12.myworkdayjobs.com')),row(External_Job_Posting_Site=URL+'?redirect=other')]))
  factory=Mock(return_value=data_client);self.assertEqual(public_search(client,factory),{'JR12345':URL});self.assertEqual(client.discovery_dates,{'JR12345':'2026-11-12'});factory.assert_called_once_with('a.sfdcstatic.com')
  for changes in [{'Total_Jobs':10},{'Count':3},{'Fetch_Timestamp':(datetime.now(timezone.utc)-timedelta(days=2)).isoformat()},{'Fetch_Timestamp':'2026-11-14T00:00:00'}]:
   with self.assertRaises(ValueError):salesforce_rows(snapshot([row()],**changes))
 def test_state_and_city_come_from_explicit_employer_label_not_generic_telecommute(self):
  with patch.dict(c.SOURCES,{'salesforce':(HOST,'Technology')}):
   j=c.normalize_posting(posting(),URL,'salesforce',datetime(2026,11,14,tzinfo=timezone.utc))
   self.assertEqual(j['locations'],[{'city':'New York','state':'New York'}]);self.assertEqual(j['arrangement'],'unknown');self.assertEqual(j['eligibleStates'],[])
   j=c.normalize_posting(posting('Texas - Remote',_salesforceRemoteType='Remote - Home Based'),URL,'salesforce',datetime(2026,11,14,tzinfo=timezone.utc))
   self.assertEqual(j['arrangement'],'remote');self.assertEqual(j['remoteScope'],'states');self.assertEqual(j['eligibleStates'],['Texas'])
   self.assertIsNone(c.normalize_posting(posting('Unknown City'),URL,'salesforce',datetime(2026,11,14,tzinfo=timezone.utc)))
 def test_office_flexible_overrides_remote_location_label_and_unknown_model_is_not_guessed(self):
  with patch.dict(c.SOURCES,{'salesforce':(HOST,'Technology')}):
   for model,expected in [('Office - Flexible','hybrid'),('Office - Assigned','on-site'),('Unrecognized','unknown'),('','unknown')]:
    j=c.normalize_posting(posting('Texas - Remote',_salesforceRemoteType=model),URL,'salesforce',datetime(2026,11,14,tzinfo=timezone.utc))
    self.assertEqual(j['arrangement'],expected);self.assertEqual(j['eligibleStates'],[])
 def test_public_details_require_matching_identity_date_country_and_publication_status(self):
  info={'jobReqId':'JR12345','jobPostingSiteId':'External_Career_Site','jobPostingId':'Synthetic-Role_JR12345','externalUrl':URL,'title':'Synthetic advisor','startDate':'2026-11-12','posted':True,'canApply':True,'country':{'descriptor':'United States of America'},'location':'Texas - Remote','additionalLocations':['Washington D.C. - Remote'],'remoteType':'Office - Flexible','jobDescription':'<p>Specific role duties.</p>'}
  with patch.dict(c.SOURCES,{'salesforce':(HOST,'Technology')}):
   body=enrich(posting(),json.dumps({'jobPostingInfo':info}));j=c.normalize_posting(body,URL,'salesforce',datetime(2026,11,14,tzinfo=timezone.utc))
   self.assertEqual(j['arrangement'],'hybrid');self.assertEqual(j['collectionMethod'],'salesforce-public-role-details');self.assertEqual({l['state'] for l in j['locations']},{'Texas','District of Columbia'})
   closed=enrich(posting(),json.dumps({'jobPostingInfo':{**info,'canApply':False}}));self.assertEqual(c.normalize_posting(closed,URL,'salesforce',datetime(2026,11,14,tzinfo=timezone.utc))['status'],'closed')
  for changes in [{'jobReqId':'JR999'},{'startDate':'2026-11-11'},{'externalUrl':URL.replace(HOST,'other.example')},{'posted':None},{'country':{'descriptor':'Canada'}}]:
   with self.assertRaises(ValueError):enrich(posting(),json.dumps({'jobPostingInfo':{**info,**changes}}))
 def test_multiple_location_pay_bands_do_not_become_one_numeric_range(self):
  with patch.dict(c.SOURCES,{'salesforce':(HOST,'Technology')}):
   j=c.normalize_posting(posting(description='The typical base salary range for this position is $100,000 - $150,000 annually. In select cities the base salary range for this role is $120,000 - $170,000 annually.'),URL,'salesforce',datetime(2026,11,14,tzinfo=timezone.utc))
   self.assertIsNone(j['salary']);self.assertIn('$120,000',j['publishedPay']['text'])
