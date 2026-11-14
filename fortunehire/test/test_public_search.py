"""Synthetic public search fixtures; not published as employer data."""
import sys,json,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from unittest.mock import Mock,patch
from datetime import datetime,timezone
import collect_jobs as c
from employer_sources import public_search,public_fetch
URL='https://www.amazon.jobs/en/jobs/12345/test-role'
NOW=datetime(2026,11,14,15,tzinfo=timezone.utc)
def record(**kw):
 d={'id_icims':'12345','job_path':'/en/jobs/12345/test-role','title':'Synthetic support engineer','country_code':'USA','posted_date':'November 14, 2026','job_schedule_type':'full-time','locations':[json.dumps({'countryIso2a':'US','normalizedStateName':'California','city':'Test City','type':'ONSITE'})]};d.update(kw);return d
def page(**kw):
 return '<meta property="og:url" content="'+kw.get('url',URL)+'"><h1 class="title">'+kw.get('title','Synthetic support engineer')+'</h1><div id="job-detail-body"><div class="content"><p>'+kw.get('description','Role duties.')+'</p></div></div><aside>Work Type: Remote</aside>'
class PublicSearchTests(unittest.TestCase):
 def test_ups_current_search_uses_posting_date_and_real_route_id(self):
  req='1ece6f35-c3ec-40e5-acc6-5546a27d1eae';cl=Mock(host='www.jobs-ups.com')
  payload={'eagerLoadRefineSearch':{'totalHits':200,'data':{'jobs':[{'jobId':req,'title':'Synthetic Driver Helper','country':'United States of America','postedDate':'2026-11-13','dateCreated':'2025-01-01'}]}}}
  cl.get.return_value=(200,'<script>phApp.ddo = '+json.dumps(payload)+';</script>')
  self.assertEqual(public_search(cl,Mock()),{req:'https://www.jobs-ups.com/us/en/job/'+req+'/Synthetic-Driver-Helper'})
  self.assertEqual(cl.discovery_dates[req],'2026-11-13');self.assertTrue(cl.discovery_limited)
 def test_reviewed_policy_redirect_does_not_allow_foreign_job_redirects(self):
  redirect=c.RestrictedRedirect('careers.salesforce.com');target='https://www.salesforce.com/404/'
  req=c.urllib.request.Request('https://careers.salesforce.com/robots.txt')
  self.assertEqual(redirect.redirect_request(req,None,301,'Moved',{},target).full_url,target)
  for url in ['https://careers.salesforce.com/en/jobs/123/role','https://careers.salesforce.com/']:
   with self.assertRaises(ValueError):redirect.redirect_request(c.urllib.request.Request(url),None,301,'Moved',{},target)
  with self.assertRaises(ValueError):redirect.redirect_request(req,None,301,'Moved',{},'https://other.example/robots.txt')
 def test_amazon_search_is_bounded_us_only_and_uses_real_posting_dates(self):
  cl=Mock(host='www.amazon.jobs');cl.get.return_value=(200,json.dumps({'error':None,'hits':200,'jobs':[record(),record(id_icims='999',job_path='/en/jobs/999/foreign',country_code='IND'),record(id_icims='OTHER')]}))
  self.assertEqual(public_search(cl,Mock()),{'12345':URL});self.assertEqual(cl.discovery_dates['12345'],'2026-11-14');self.assertTrue(cl.discovery_limited)
 def test_amazon_existing_job_id_lookup_and_page_identity_are_verified(self):
  cl=Mock(host='www.amazon.jobs');cl.amazon_records={};cl.get.side_effect=[(200,page()),(200,json.dumps({'jobs':[record()],'error':None}))]
  status,body=public_fetch(cl,URL,Mock());self.assertIn('base_query=12345',cl.get.call_args.args[0])
  with patch.dict(c.SOURCES,{'amazon':('www.amazon.jobs','Consumer Discretionary')}):
   job=c.normalize_posting(body,URL,'amazon',NOW)
   self.assertEqual(job['postedAt'],'2026-11-14');self.assertEqual(job['arrangement'],'unknown');self.assertEqual(job['remoteScope'],'unknown');self.assertEqual(job['identifierType'],'posting-id')
 def test_amazon_never_fills_missing_identity_or_date_and_preserves_404(self):
  cl=Mock(host='www.amazon.jobs');cl.amazon_records={'12345':record()};cl.get.return_value=(200,page(title='Another role'))
  with self.assertRaises(ValueError):public_fetch(cl,URL,Mock())
  cl.get.return_value=(404,'');self.assertEqual(public_fetch(cl,URL,Mock()),(404,''))
  cl.get.return_value=(200,page());cl.amazon_records={'12345':record(posted_date='unknown')}
  status,body=public_fetch(cl,URL,Mock())
  with patch.dict(c.SOURCES,{'amazon':('www.amazon.jobs','Consumer Discretionary')}):
   with self.assertRaises(ValueError):c.normalize_posting(body,URL,'amazon',NOW)
 def test_amazon_title_whitespace_is_not_a_different_posting(self):
  cl=Mock(host='www.amazon.jobs');cl.amazon_records={'12345':record(title='Synthetic support engineer ')};cl.get.return_value=(200,page())
  status,body=public_fetch(cl,URL,Mock());self.assertEqual(json.loads(body)['amazonPosting']['title'],'Synthetic support engineer')
 def test_amazon_location_pay_periods_and_multiple_bands_remain_distinct(self):
  location=[{'city':'Test City','state':'California'}];label='The base salary range for this position is listed below.\n'
  salary,pay=c.extract_published_pay(label+'USA, CA, Test City - 33.26 - 49.51 USD hourly',location,'amazon')
  self.assertEqual(salary['period'],'hour');self.assertEqual(salary['min'],33.26)
  salary,pay=c.extract_published_pay(label+'USA, CA, Test City - 80,000 - 120,000 USD annually',location,'amazon');self.assertEqual(salary['period'],'year')
  salary,pay=c.extract_published_pay(label+'USA, CA, Test City - 80,000 - 120,000 USD annually\nUSA, WA, Other City - 90,000 - 140,000 USD annually',location,'amazon');self.assertIsNone(salary);self.assertIn('Other City',pay['text'])
 def test_costco_search_prioritizes_posted_date_not_sitemap_changes(self):
  cl=Mock(host='careers.costco.com');cl.get.return_value=(200,json.dumps({'totalCount':19000,'jobs':[{'data':{'req_id':'123','slug':'123','country':'United States','posted_date':'2026-11-12'}},{'data':{'req_id':'456','slug':'789','country':'United States'}}]}))
  self.assertEqual(public_search(cl,Mock()),{'123':'https://careers.costco.com/jobs/123'});self.assertEqual(cl.discovery_dates['123'],'2026-11-12');self.assertTrue(cl.discovery_limited)
  self.assertIn('posted_date',cl.get.call_args.args[0])
 def test_costco_explicit_hourly_range_supports_pay_filter_but_year_bands_do_not(self):
  loc=[{'city':'Test City','state':'Washington'}]
  salary,pay=c.extract_published_pay('Salary Range: $21.00/hr - $32.90/hr',loc,'costco');self.assertEqual(salary['period'],'hour');self.assertEqual(salary['min'],21)
  salary,pay=c.extract_published_pay('Salary Range: 1st year intern $25/hr',loc,'costco');self.assertIsNone(salary)
if __name__=='__main__':unittest.main()
