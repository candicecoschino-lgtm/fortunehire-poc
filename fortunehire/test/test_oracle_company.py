import sys,json,unittest
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import collect_jobs as c
from employer_adapters import oracle
URL='https://careers.oracle.com/en/sites/jobsearch/job/12345'
def data(**changes):
 row={'Id':'12345','Title':'Synthetic writer-HYBRID','ExternalPostedStartDate':'2026-11-16T02:40:38+00:00','ExternalDescriptionStr':'Travel: 25%.','PrimaryLocationCountry':'US','PrimaryLocation':'Reston, VA, United States','secondaryLocations':[{'Name':'Washington, DC, United States','CountryCode':'US'},{'Name':'London, England, United Kingdom','CountryCode':'GB'}],'workLocation':[],'otherWorkLocations':[]};row.update(changes);return json.dumps({'items':[row]})
class OracleCompanyTests(unittest.TestCase):
 def test_public_named_locations_and_explicit_title_survive_missing_work_address(self):
  with patch.dict(c.SOURCES,{'oracle':('careers.oracle.com','Technology')}):
   j=c.normalize_posting(data(),URL,'oracle',datetime(2026,11,16,tzinfo=timezone.utc))
   self.assertEqual(j['locations'],[{'city':'Reston','state':'Virginia'},{'city':'Washington','state':'District of Columbia'}]);self.assertEqual(j['arrangement'],'hybrid');self.assertTrue(j['travelRequired']);self.assertEqual(j['postedAt'],'2026-11-15')
 def test_unknown_states_country_only_locations_and_wrong_identity_are_not_invented(self):
  with patch.dict(c.SOURCES,{'oracle':('careers.oracle.com','Technology')}):
   for label in ['United States','Remote, ZZ, United States','London, England, United Kingdom']:
    self.assertIsNone(c.normalize_posting(data(PrimaryLocation=label,secondaryLocations=[]),URL,'oracle',datetime(2026,11,16,tzinfo=timezone.utc)))
  self.assertIsNone(oracle(data(Id='999'),URL))
 def test_named_location_fallback_is_scoped_to_oracles_reviewed_format(self):
  self.assertEqual(oracle(data(),'https://enterpriseplatform.dell.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/12345')['jobLocation'],[])
