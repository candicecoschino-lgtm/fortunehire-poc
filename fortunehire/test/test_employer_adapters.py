"""Synthetic fixtures for reviewed public-page formats; never published."""
import sys,json,unittest
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import collect_jobs as c
NOW=datetime(2026,11,13,21,tzinfo=timezone.utc)
WALMART='https://careers.walmart.com/us/en/jobs/R-TEST-1'
def walmart(status='OPEN',req='R-TEST-1'):
    job={'jobId':req,'title':'Synthetic warehouse role','requisitionStatus':{'id':status},'active':False,'jobPostingStartDate':'2026-11-12','jobPostingDescription':'Pay information is published separately.','employmentTypes':[{'value':'Full time'}],'primaryLocation':{'city':'Test City','stateCode':'TX','countryCode':'US'},'payRange':[{'min':'20.60','max':'24.10'}],'payFrequency':'Hourly','payPlanData':{'currencyReference':{'currencyId':'USD'}}}
    return '<script id=__NEXT_DATA__ type="application/json">'+json.dumps({'props':{'pageProps':{'jobId':req,'jobDetails':job}}})+'</script>'
class AdapterTests(unittest.TestCase):
    def test_walmart_identity_status_pay_and_posting_date(self):
        with patch.dict(c.SOURCES,{'walmart':('careers.walmart.com','Retail')}):
            j=c.normalize_posting(walmart(),WALMART,'walmart',NOW)
            self.assertEqual(j['status'],'reviewed');self.assertEqual(j['postedAt'],'2026-11-12')
            self.assertEqual(j['salary']['period'],'hour');self.assertEqual(j['salary']['min'],20.6)
            self.assertEqual(j['arrangement'],'unknown');self.assertEqual(j['salary']['scopeStates'],['Texas'])
            self.assertEqual(c.normalize_posting(walmart('CLOSED'),WALMART,'walmart',NOW)['status'],'closed')
            with self.assertRaises(ValueError):c.normalize_posting(walmart(req='R-OTHER'),WALMART,'walmart',NOW)
            with self.assertRaises(ValueError):c.normalize_posting(walmart(status='UNKNOWN'),WALMART,'walmart',NOW)

    def test_disney_primary_metadata_and_description_are_scoped(self):
        url='https://www.disneycareers.com/en/job/test/role/391/12345'
        doc='<div id="job-details-1" data-job-id="12345" data-tm-job-id="REQ-1" data-tm-job-name="Synthetic Intern" data-tm-job-location="Test City, California, United States / Foreign City, Ontario, Canada" data-tm-job-date-posted="11/12/2026"></div><section id="job-details-3"><p>Role Type: Hybrid</p></section><aside>Role Type: Remote</aside>'
        with patch.dict(c.SOURCES,{'disney':('www.disneycareers.com','Entertainment')}):
            j=c.normalize_posting(doc,url,'disney',NOW)
            self.assertEqual(j['arrangement'],'hybrid');self.assertEqual(j['postedAt'],'2026-11-12')
            self.assertEqual(j['locations'],[{'city':'Test City','state':'California'}])
            with self.assertRaises(ValueError):c.normalize_posting(doc.replace('data-job-id="12345"','data-job-id="99999"'),url,'disney',NOW)

    def test_workday_missing_url_requires_matching_requisition(self):
        host='coke.wd1.myworkdayjobs.com';url='https://'+host+'/coca-cola-careers/job/US---GA---Atlanta/Test_R-12345'
        data={'@type':'JobPosting','identifier':{'value':'R-12345'},'title':'Synthetic specialist','datePosted':'2026-11-12','description':'Job description.','jobLocation':{'address':{'addressCountry':'United States of America','addressLocality':'US - GA - Atlanta'}}}
        document='<script type="application/ld+json">'+json.dumps(data)+'</script>'
        with patch.dict(c.SOURCES,{'coca-cola':(host,'Consumer Goods')}):
            j=c.normalize_posting(document,url,'coca-cola',NOW)
            self.assertEqual(j['locations'],[{'city':'Atlanta','state':'Georgia'}])
            with self.assertRaises(ValueError):c.normalize_posting(document,url.replace('R-12345','R-OTHER'),'coca-cola',NOW)
            self.assertNotEqual(c.posting_key(url),c.posting_key(url.replace('R-12345','R-99999')))

    def test_opaque_ids_and_translated_cisco_pages_are_not_chronology(self):
        self.assertEqual(c.discovery_priority('96685732-a40b-4567-be51-238f2e34272c'),(0,''))
        first='https://careers.cisco.com/global/en/job/CISCISGLOBAL2030568EXTERNALENGLOBAL/Title'
        second='https://careers.cisco.com/ca/fr/job/CISCISGLOBAL2030568EXTERNALFRCA/Titre'
        self.assertEqual(c.posting_key(first),c.posting_key(second))
        self.assertGreater(c.language_priority(first),c.language_priority(second))
        cardinal='https://jobs.cardinalhealth.com/search/jobdetails/test-role/96685732-a40b-4567-be51-238f2e34272c'
        self.assertEqual(c.job_url(cardinal,'jobs.cardinalhealth.com'),cardinal)
        self.assertEqual(c.posting_key(cardinal),'96685732-a40b-4567-be51-238f2e34272c')

    def test_long_pay_text_keeps_currency_band_visible(self):
        salary,published=c.extract_published_pay('Job duties. '*150+'Pay Range: United States: 193,000 - 224,000 USD Base pay depends on geography.',[{'city':'Atlanta','state':'Georgia'}],'coca-cola')
        self.assertIsNone(salary);self.assertIn('193,000',published['text']);self.assertNotIn('Job duties',published['text'])

    def test_explicit_national_remote_does_not_require_an_office_address(self):
        from test_collector import body,URL
        document=body(jobLocation=[],jobLocationType='TELECOMMUTE',applicantLocationRequirements={'@type':'Country','name':'United States'})
        job=c.normalize_posting(document,URL,'boeing',NOW)
        self.assertEqual(job['remoteScope'],'nationwide');self.assertEqual(job['locations'],[])
        self.assertEqual(job['locationNote'],'Remote within the U.S.')

if __name__=='__main__':unittest.main()
