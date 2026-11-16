"""Unavailable employer postings and brief gateway failures must stay distinct."""
import sys,json,unittest
from pathlib import Path
from datetime import timedelta
from unittest.mock import Mock,MagicMock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import collect_jobs as c
from employer_sources import public_fetch,workday_unavailable
import test_collector as fixtures
from test_collector import URL,NOW,body

SF='https://salesforce.wd12.myworkdayjobs.com/External_Career_Site/job/Texas---Remote/Example_JR12345'
COKE='https://coke.wd1.myworkdayjobs.com/en-US/coca-cola-careers/job/Example_R-12345'
def shell(url,tenant='salesforce',site='External_Career_Site',available='false'):
 return '<meta property="og:url" content="'+url+'"><script>window.workday = window.workday || {tenant: "'+tenant+'",siteId: "'+site+'",appName: "cxs",isExternal: true,postingAvailable: '+available+',allowedFileTypes: []};</script><div id="root"></div>'

class RefreshRepairTests(unittest.TestCase):
 def test_reviewed_workday_unavailable_is_missing_without_calling_details_api(self):
  for url,tenant,site in [(SF,'salesforce','External_Career_Site'),(COKE,'coke','coca-cola-careers')]:
   client=Mock(host=c.urllib.parse.urlsplit(url).hostname);client.get.return_value=(200,shell(url,tenant,site))
   self.assertEqual(public_fetch(client,url,Mock()),(404,''));client.get.assert_called_once_with(url)
 def test_ambiguous_or_mismatched_shell_cannot_establish_missing_job(self):
  good=shell(SF)
  for invalid in [good.replace('postingAvailable: false','postingAvailable: true'),good.replace('tenant: "salesforce"','tenant: "another"'),good.replace('siteId: "External_Career_Site"','siteId: "Internal"'),good.replace('isExternal: true','isExternal: false'),good.replace('appName: "cxs"','appName: "login"'),good.replace('postingAvailable: false','postingAvailable: false,postingAvailable: true'),good.replace(SF,SF+'-1'),good+'<script type="application/ld+json">{}</script>','<div id="root"></div>']:
   self.assertFalse(workday_unavailable(invalid,SF))
  self.assertFalse(workday_unavailable(good,SF+'?redirect=other'))
  self.assertFalse(workday_unavailable(good.replace('salesforce.wd12.myworkdayjobs.com','unreviewed.myworkdayjobs.com'),SF.replace('salesforce.wd12.myworkdayjobs.com','unreviewed.myworkdayjobs.com')))
 def test_missing_signal_preserves_date_and_requires_two_checks_six_hours_apart(self):
  old=c.normalize_posting(body(),URL,'boeing',NOW)
  jobs,state,r=c.reconcile('boeing',[old],{}, {},lambda u:(404,''),NOW)
  self.assertEqual(r['closed'],0);self.assertEqual(jobs[0]['reviewedAt'],old['reviewedAt'])
  jobs,state,r=c.reconcile('boeing',jobs,state,{},lambda u:(404,''),NOW+timedelta(hours=5))
  self.assertEqual(r['closed'],0)
  jobs,state,r=c.reconcile('boeing',jobs,state,{},lambda u:(404,''),NOW+timedelta(hours=6))
  self.assertEqual(r['closed'],1)
 def test_gateway_failure_recovers_with_bounded_backoff(self):
  cl=fixtures.CollectorTests().client_without_network();response=MagicMock();response.__enter__.return_value.status=200;response.__enter__.return_value.read.return_value=b'complete'
  cl.opener.open.side_effect=[c.urllib.error.HTTPError(URL,502,'Gateway',{},None),response]
  with patch('collect_jobs.time.sleep') as sleep:self.assertEqual(cl.get(URL),(200,'complete'));self.assertIn(unittest.mock.call(2),sleep.call_args_list)
  self.assertEqual(cl.opener.open.call_count,2)
 def test_retry_after_is_honored_but_long_wait_denials_and_challenges_stop(self):
  for code,headers,expected in [(503,{'Retry-After':'7'},3),(504,{},3),(503,{'Retry-After':'120'},1),(503,{'Retry-After':'invalid'},1),(503,{'Cf-Mitigated':'challenge'},1),(403,{},1),(429,{'Retry-After':'1'},1)]:
   cl=fixtures.CollectorTests().client_without_network();cl.opener.open.side_effect=c.urllib.error.HTTPError(URL,code,'Failure',headers,None)
   with patch('collect_jobs.time.sleep') as sleep,self.assertRaises(c.SourceError):cl.get(URL)
   self.assertEqual(cl.opener.open.call_count,expected)
   if headers.get('Retry-After')=='7':self.assertIn(unittest.mock.call(7),sleep.call_args_list)
