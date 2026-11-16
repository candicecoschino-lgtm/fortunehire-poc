import sys,unittest,urllib.error
from pathlib import Path
from unittest.mock import Mock,MagicMock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import collect_jobs as c
from jpm_public import allowed,create,HOST,BASE,API
class ScopeTests(unittest.TestCase):
 def test_private_applicant_wrong_tenant_and_other_hosts_are_never_allowed(self):
  for path in ['/hcmRestApi/resources/11.13.18.05/candidates','/login',BASE+'/job/123?token=private',BASE.replace('CX_1001','CX_OTHER')+'/job/123']:
   self.assertFalse(allowed('https://'+HOST+path))
  self.assertFalse(allowed('https://other.example'+BASE+'/job/123'));self.assertTrue(allowed('https://'+HOST+BASE+'/job/123'))
 def test_actual_job_denials_are_not_retried_even_after_approved_policy_exception(self):
  robots='https://'+HOST+'/robots.txt';job='https://'+HOST+BASE+'/job/123';opener=Mock();opener.open.side_effect=[urllib.error.HTTPError(robots,403,'Denied',{},None),urllib.error.HTTPError(job,403,'Denied',{},None)]
  with patch.object(c.urllib.request,'build_opener',return_value=opener),patch.object(c.time,'sleep'):
   client=create(c.Client,c.SourceError,approved=True)
   with self.assertRaises(c.SourceError):client.get(job)
   self.assertEqual(opener.open.call_count,2)
 def test_rate_limits_server_failures_and_unapproved_policy_exceptions_stop(self):
  robots='https://'+HOST+'/robots.txt'
  for code,approved in [(429,True),(503,True),(403,False)]:
   opener=Mock();opener.open.side_effect=urllib.error.HTTPError(robots,code,'Unavailable',{},None)
   with patch.object(c.urllib.request,'build_opener',return_value=opener),patch.object(c.time,'sleep'),self.assertRaises(c.SourceError):create(c.Client,c.SourceError,approved=approved)
 def test_successfully_loaded_exclusions_remain_effective(self):
  opener=Mock();response=MagicMock();response.__enter__.return_value.status=200;response.__enter__.return_value.read.return_value=b'User-agent: *\nDisallow: /';opener.open.return_value=response
  with patch.object(c.urllib.request,'build_opener',return_value=opener),patch.object(c.time,'sleep'):
   client=create(c.Client,c.SourceError,approved=True)
   with self.assertRaises(c.SourceError):client.get('https://'+HOST+BASE+'/job/123')
   self.assertEqual(opener.open.call_count,1)
 def test_policy_checks_cannot_be_disabled_for_job_requests(self):
  robots='https://'+HOST+'/robots.txt';opener=Mock();opener.open.side_effect=urllib.error.HTTPError(robots,403,'Denied',{},None)
  with patch.object(c.urllib.request,'build_opener',return_value=opener),patch.object(c.time,'sleep'):
   client=create(c.Client,c.SourceError,approved=True)
   with self.assertRaises(c.SourceError):client.get('https://'+HOST+BASE+'/job/123',check=False)
   self.assertEqual(opener.open.call_count,1)

if __name__=='__main__':unittest.main()
