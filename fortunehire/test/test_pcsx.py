"""Synthetic public employer fixtures, never published."""
import sys,json,unittest
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import collect_jobs as c
from pcsx_public import enrich,discover,fetch
HOST='apply.careers.microsoft.com';URL='https://'+HOST+'/careers/job/12345';STAMP=datetime(2026,11,14,tzinfo=timezone.utc).timestamp()
def api(**kw):
 d={'id':12345,'atsJobId':'REQ123','displayJobId':'REQ123','name':'Synthetic engineer','positionUrl':'/careers/job/12345','publicUrl':URL,'postedTs':STAMP,'creationTs':STAMP+864000,'locations':['United States, Washington, Redmond'],'jobDescription':'The salary range for this role is $100,000 - $150,000 per year.','workLocationOption':'onsite','efcustomTextWorkSite':['3 days / week in-office'],'efcustomTextRequiredTravel':['Less than 25%']};d.update(kw);return d
def envelope(d):return json.dumps({'status':200,'error':{'message':''},'data':d})
def page(**kw):
 d={'@type':'JobPosting','title':'Synthetic engineer','url':URL,'datePosted':'2026-11-14T00:00:00','employmentType':'FULL_TIME','validThrough':'2027-05-13'};d.update(kw);return '<script type="application/ld+json">'+json.dumps(d)+'</script>'
class PcsxTests(unittest.TestCase):
 def test_role_worksite_beats_broad_office_flag_and_preserves_pay_travel_and_posting_date(self):
  body=enrich(page(),envelope(api()),URL,HOST)
  with patch.dict(c.SOURCES,{'microsoft':(HOST,'Technology')}):
   j=c.normalize_posting(body,URL,'microsoft',datetime(2026,11,15,tzinfo=timezone.utc))
   self.assertEqual(j['arrangement'],'hybrid');self.assertTrue(j['travelRequired']);self.assertEqual(j['postedAt'],'2026-11-14');self.assertEqual(j['locations'],[{'city':'Redmond','state':'Washington'}]);self.assertEqual(j['salary']['min'],100000);self.assertIsNone(j['closesAt']);self.assertEqual(j['requisitionId'],'REQ123');self.assertIn('3 days',j['evidence']['arrangement'])
 def test_nvidia_remote_requires_role_setting_and_eligible_states_require_remote_location(self):
  host='jobs.nvidia.com';url=URL.replace(HOST,host)
  data=api(publicUrl=url,locations=['US, CA, Remote','US, NY, New York'],workLocationOption='remote')
  with patch.dict(c.SOURCES,{'nvidia':(host,'Technology')}):
   j=c.normalize_posting(enrich(page(url=url),envelope(data),url,host),url,'nvidia',datetime(2026,11,15,tzinfo=timezone.utc))
   self.assertEqual(j['arrangement'],'remote');self.assertEqual(j['eligibleStates'],['California']);self.assertEqual(j['remoteScope'],'states')
   data['workLocationOption']='onsite';j=c.normalize_posting(enrich(page(url=url),envelope(data),url,host),url,'nvidia',datetime(2026,11,15,tzinfo=timezone.utc));self.assertEqual(j['arrangement'],'unknown');self.assertEqual(j['eligibleStates'],[])
 def test_wrong_identity_host_title_or_date_is_rejected_instead_of_using_creation_time(self):
  for changes in [{'id':999},{'atsJobId':'OTHER'},{'publicUrl':URL.replace(HOST,'other.example')},{'name':'Different role'},{'postedTs':STAMP+86400},{'postedTs':None}]:
   with self.assertRaises(ValueError):enrich(page(),envelope(api(**changes)),URL,HOST)
 def test_unverified_national_location_does_not_invent_a_state_or_nationwide_eligibility(self):
  d=api(locations=['United States, Multiple Locations, Multiple Locations'],efcustomTextWorkSite=['0 days / week in-office – remote'])
  with patch.dict(c.SOURCES,{'microsoft':(HOST,'Technology')}):self.assertIsNone(c.normalize_posting(enrich(page(),envelope(d),URL,HOST),URL,'microsoft',datetime(2026,11,15,tzinfo=timezone.utc)))
 def test_search_validates_host_posting_id_us_location_and_actual_posting_timestamp(self):
  client=Mock(host=HOST);client.get.return_value=(200,envelope({'positions':[api(),api(id=7,positionUrl='/careers/job/7',locations=['Ireland, Dublin, Dublin']),api(id=8,positionUrl='/careers/job/999')],'count':3}))
  self.assertEqual(discover(client),{'12345':URL});self.assertEqual(client.discovery_dates,{'12345':'2026-11-14'});self.assertIn('sort_by=timestamp',client.get.call_args.args[0])
 def test_individual_refresh_uses_independent_position_id_lookup_and_explicit_missing_status(self):
  cl=Mock(host=HOST);cl.get.return_value=(200,envelope(api()));status,body=fetch(cl,URL,page());self.assertEqual(status,200);self.assertIn('position_id=12345',cl.get.call_args.args[0]);self.assertIn('REQ123',body)
  cl.get.return_value=(200,json.dumps({'status':404,'error':{'message':'Position not found'}}));self.assertEqual(fetch(cl,URL,page()),(404,''))
