"""Synthetic fixtures; no synthetic jobs are published."""
import sys,json,unittest
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch,Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import collect_jobs as c
from employer_sources import public_search
from apple_public import extract
URL='https://jobs.apple.com/en-us/details/123456-0017/synthetic-role'
def source():
 return {'jobNumber':'123456-0017','postingTitle':'Synthetic engineer','description':'Role duties.','selectedLocation':{'id':'postLocation-TST','active':True,'countryID':'iso-country-USA','city':'Test City','stateProvince':'Texas','postingIdentifier':'0017'},'postingPostLocationData':{'en_US':{'postLocation-TST':{'postingDate':'2026-11-12T01:00:00+00:00'}}},'postingDateMeta':'2026-11-14','homeOffice':False,'postingFooters':[{'postLocationId':'postLocation-OTHER','localizations':{'en_US':[{'name':'Pay & Benefits','content':'Base pay $100,000 - $200,000 a year'}]}}]}
def body(s):return '<script>window.__staticRouterHydrationData = JSON.parse('+json.dumps(json.dumps({'loaderData':{'role':s}}))+');</script><aside>Work Type: Remote</aside>'
class AppleTests(unittest.TestCase):
 def test_selected_office_pay_is_preserved_without_inventing_an_annual_period(self):
  s=source();s['postingFooters']=[{'postLocationId':'postLocation-TST','localizations':{'en_US':[{'name':'Pay & Benefits','content':'The base pay range for this role is between $100,000 and $200,000. Other benefits are separate.'}]}}]
  with patch.dict(c.SOURCES,{'apple':('jobs.apple.com','Technology')}):
   j=c.normalize_posting(body(s),URL,'apple',datetime(2026,11,14,tzinfo=timezone.utc))
   self.assertIsNone(j['salary']);self.assertIn('$100,000',j['publishedPay']['text']);self.assertEqual(j['publishedPay']['scopeStates'],['Texas'])
 def test_location_date_overrides_general_display_date_and_other_location_pay_is_excluded(self):
  with patch.dict(c.SOURCES,{'apple':('jobs.apple.com','Technology')}):
   j=c.normalize_posting(body(source()),URL,'apple',datetime(2026,11,14,tzinfo=timezone.utc))
   self.assertEqual(j['postedAt'],'2026-11-12');self.assertEqual(j['requisitionId'],'123456-0017');self.assertEqual(j['locations'],[{'city':'Test City','state':'Texas'}]);self.assertEqual(j['arrangement'],'unknown');self.assertIsNone(j['publishedPay']);self.assertEqual(j['eligibleStates'],[])
 def test_no_fallback_to_display_date_or_country_only_pipeline(self):
  for key in ('postingPostLocationData','selectedLocation'):
   s=source();s.pop(key);self.assertIsNone(extract(body(s),URL))
  s=source();s['selectedLocation']['postingIdentifier']='9999';self.assertIsNone(extract(body(s),URL))
  s=source();s['selectedLocation']['countryID']='iso-country-CAN';self.assertIsNone(extract(body(s),URL))
  self.assertIsNone(extract(body(source()),URL.replace('123456-0017','999999-0017')))
 def test_search_uses_only_individual_role_paths_and_preserves_location_suffix(self):
  cl=Mock(host='jobs.apple.com');cl.get.return_value=(200,'<a href="'+URL+'?team=TEST">Role</a><a href="'+URL+'/locationPicker">Locations</a><a href="https://other.example/en-us/details/1/role">Other</a>')
  self.assertEqual(public_search(cl,Mock()),{'123456-0017':URL});self.assertEqual(c.posting_key(URL),'123456-0017')
  for bad in (URL+'/locationPicker','https://jobs.apple.com/en-us/search'):
   with self.assertRaises(ValueError):c.job_url(bad,'jobs.apple.com')
 def test_only_exact_corporate_robots_redirects_are_followed(self):
  h=c.RestrictedRedirect('jobs.apple.com')
  for old,new in [('https://jobs.apple.com/robots.txt','https://apple.com/pagenotfound'),('https://apple.com/pagenotfound','https://www.apple.com/pagenotfound')]:
   self.assertEqual(h.redirect_request(c.urllib.request.Request(old),None,301,'Moved',{},new).full_url,new)
  with self.assertRaises(ValueError):h.redirect_request(c.urllib.request.Request(URL),None,301,'Moved',{},'https://www.apple.com/pagenotfound')
