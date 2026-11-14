import sys,json,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from unittest.mock import patch
from datetime import datetime,timezone
import collect_jobs as c
HOST='fanniemae.wd1.myworkdayjobs.com'
URL='https://'+HOST+'/FannieMaeCareers/job/Washington-DC/Synthetic-Role_JR123'
CANONICAL='https://'+HOST+'/en-US/FannieMaeCareers/job/Synthetic-Role_JR123'
NOW=datetime(2026,11,14,18,tzinfo=timezone.utc)
def body(locations=None):
 job={'@type':'JobPosting','identifier':{'value':'JR123'},'title':'Synthetic advisor','datePosted':'2026-11-13','jobLocation':locations or {'address':{'addressCountry':'United States of America','addressLocality':'Midtown Center'}},'jobLocationType':'TELECOMMUTE','applicantLocationRequirements':{'@type':'Country','name':'United States of America'},'description':'For most roles, employees are expected to work onsite on a regular basis.'}
 return '<link rel="canonical" href="'+CANONICAL+'"><script type="application/ld+json">'+json.dumps(job)+'</script>'
class FannieTests(unittest.TestCase):
 def test_annual_hiring_range_requires_explicit_period_and_one_state(self):
  loc=[{'city':'Midtown Center','state':'District of Columbia'}]
  salary,pay=c.extract_published_pay('Target Pay Range: $155,000.00 - 209,000.00 a year',loc,'fannie-mae')
  self.assertEqual(salary['period'],'year');self.assertEqual(salary['min'],155000);self.assertEqual(salary['scopeStates'],['District of Columbia'])
  salary,pay=c.extract_published_pay('Pay Range: $141,000 - $184,000 per year',loc,'fannie-mae');self.assertEqual(salary['max'],184000)
  salary,pay=c.extract_published_pay('Pay Range: $141,000 - $184,000',loc,'fannie-mae');self.assertIsNone(salary)
  salary,pay=c.extract_published_pay('Pay Range: $141,000 - $184,000 a year',loc+[{'city':'Other Office','state':'Virginia'}],'fannie-mae');self.assertIsNone(salary)
 def test_single_office_uses_requested_employer_state_even_when_canonical_drops_it(self):
  with patch.dict(c.SOURCES,{'fannie-mae':(HOST,'Financials')}):
   j=c.normalize_posting(body(),URL,'fannie-mae',NOW)
   self.assertEqual(j['url'],CANONICAL);self.assertEqual(j['locations'],[{'city':'Midtown Center','state':'District of Columbia'}])
   self.assertEqual(j['arrangement'],'unknown');self.assertEqual(j['remoteScope'],'unknown');self.assertEqual(j['eligibleStates'],[])
   self.assertIn(URL,j['evidence']['location'])
 def test_no_state_guess_for_unknown_or_multiple_offices(self):
  with patch.dict(c.SOURCES,{'fannie-mae':(HOST,'Financials')}):
   self.assertIsNone(c.normalize_posting(body(),URL.replace('Washington-DC','Unknown-XX'),'fannie-mae',NOW))
   offices=[{'address':{'addressCountry':'US','addressLocality':name}} for name in ['Midtown Center','Plano Office']]
   self.assertIsNone(c.normalize_posting(body(offices),URL,'fannie-mae',NOW))
