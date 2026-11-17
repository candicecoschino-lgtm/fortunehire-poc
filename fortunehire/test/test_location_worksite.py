"""Location-based defaults are disclosed and never override stated work models."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import collect_jobs as c
from location_worksite import use_listed_location,apply_location_policy,LOCATION_REASON
from test_collector import body,URL,NOW

class LocationWorksiteTests(unittest.TestCase):
 def test_city_and_state_supply_the_user_selected_onsite_default(self):
  j=apply_location_policy(c.normalize_posting(body(description='Role responsibilities and qualifications.'),URL,'boeing',NOW))
  self.assertEqual(j['arrangement'],'on-site');self.assertEqual(j['arrangementBasis'],'listed-location')
  self.assertEqual(j['evidence']['arrangement'],'');self.assertEqual(j['arrangementNote'],LOCATION_REASON)
  self.assertEqual(j['postedAt'],'2026-11-12');self.assertEqual(j['locations'],[{'city':'Test City','state':'Florida'}])
 def test_explicit_work_arrangements_are_never_replaced_by_the_default(self):
  for description,expected in [('This is a remote role.','remote'),('This is a hybrid role.','hybrid'),('This position is expected to be 100% onsite.','on-site')]:
   j=apply_location_policy(c.normalize_posting(body(description=description),URL,'boeing',NOW))
   self.assertEqual(j['arrangement'],expected);self.assertNotIn('arrangementBasis',j)
 def test_remote_placeholders_state_only_and_conflicting_evidence_do_not_become_onsite(self):
  for city in ['Remote','Remote - TX','Multiple Locations','Various Cities','Nationwide','Virtual','United States','Florida','Unknown','']:
   self.assertFalse(use_listed_location('unknown',[{'city':city,'state':'Florida'}]))
  self.assertFalse(use_listed_location('unknown',[{'city':'Miami','state':'Florida'}],'Conflicting employer work settings'))
  self.assertFalse(use_listed_location('unknown',[]))
 def test_existing_hybrid_and_remote_evidence_stays_authoritative(self):
  locations=[{'city':'Miami','state':'Florida'}]
  for arrangement in ['hybrid','remote','on-site']:self.assertFalse(use_listed_location(arrangement,locations))
 def test_new_york_city_is_a_real_city_even_though_it_matches_the_state_name(self):
  self.assertTrue(use_listed_location('unknown',[{'city':'New York','state':'New York'}]))
 def test_literal_remote_location_is_not_an_office_or_nationwide_eligibility(self):
  old={'companyId':'cencora','arrangement':'unknown','locations':[{'city':'Remote','state':'Florida'},{'city':'Philadelphia','state':'Pennsylvania'}],'locationNote':'Remote, Florida; Philadelphia, Pennsylvania','evidence':{'arrangement':''},'reviewedAt':'2026-11-12'}
  job=apply_location_policy(old)
  self.assertEqual(job['arrangement'],'remote');self.assertEqual(job['eligibleStates'],['Florida']);self.assertEqual(job['remoteScope'],'states');self.assertEqual(job['reviewedAt'],old['reviewedAt'])
  self.assertEqual(old['arrangement'],'unknown')
  self.assertEqual(apply_location_policy({**old,'companyId':'salesforce'})['arrangement'],'unknown')
 def test_ambiguous_remote_hybrid_options_stay_unresolved(self):
  j=apply_location_policy(c.normalize_posting(body(description='This position may be considered for a Remote or Hybrid work arrangement.'),URL,'boeing',NOW))
  self.assertEqual(j['arrangement'],'unknown');self.assertTrue(j['arrangementReviewRequired'])
 def test_refresh_applies_policy_without_changing_employer_source_evidence(self):
  old=c.normalize_posting(body(description='Role duties.'),URL,'boeing',NOW)
  jobs,state,report=c.reconcile('boeing',[old],{}, {},lambda u:(200,body(description='Role duties.')),NOW,max_new=0)
  self.assertEqual(jobs[0]['arrangement'],'on-site');self.assertEqual(report['changed'],1)
  self.assertEqual(jobs[0]['sourceHash'],old['sourceHash']);self.assertEqual(jobs[0]['evidence']['arrangement'],'')
