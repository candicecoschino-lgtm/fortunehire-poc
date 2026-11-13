"""Synthetic fixtures for reviewed public-page formats; never published."""
import sys,json,unittest
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
from unittest.mock import Mock
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

    def test_reviewed_remote_title_variants_keep_geography_unknown(self):
        from test_collector import body,URL
        for title in ['Director (US-Remote)','Nurse (Remote, IL License Required)','Retail Specialist - Remote -','Advisor - Work From Home']:
            job=c.normalize_posting(body(title=title,description='Role description.'),URL,'boeing',NOW)
            self.assertEqual(job['arrangement'],'remote');self.assertEqual(job['remoteScope'],'unknown')
        self.assertEqual(c.normalize_posting(body(title='Remote Sensing Engineer',description='Role description.'),URL,'boeing',NOW)['arrangement'],'unknown')

    def test_published_http_sitemap_is_upgraded_without_downgrading_jobs(self):
        client=Mock(host='www.pepsicojobs.com')
        client.robots.site_maps.return_value=['http://www.pepsicojobs.com/sitemap.xml']
        client.get.return_value=(200,'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://www.pepsicojobs.com/jobs/123</loc></url></urlset>')
        self.assertEqual(c.discover(client),{'123':'https://www.pepsicojobs.com/jobs/123'})
        client.get.assert_called_once_with('https://www.pepsicojobs.com/sitemap.xml')
        with self.assertRaises(ValueError):c.job_url('http://www.pepsicojobs.com/jobs/123','www.pepsicojobs.com')

    def test_canonical_posting_id_is_distinguished_from_a_requisition(self):
        from test_collector import body
        url='https://www.pepsicojobs.com/main/jobs/123'
        with patch.dict(c.SOURCES,{'pepsico':('www.pepsicojobs.com','Consumer Goods')}):
            job=c.normalize_posting(body(url=url,identifier=None),url,'pepsico',NOW)
            self.assertEqual(job['requisitionId'],'123');self.assertEqual(job['identifierType'],'posting-id')

    def test_legacy_sitemap_namespace_and_successfactors_identity(self):
        client=Mock(host='careers.phillips66.com')
        client.robots.site_maps.return_value=[]
        url='https://careers.phillips66.com/job/Test-City-Role/1450376900/'
        client.get.return_value=(200,'<urlset xmlns="http://www.google.com/schemas/sitemap/0.9"><url><loc>'+url+'</loc></url></urlset>')
        self.assertEqual(c.discover(client),{'1450376900':url})

    def test_foreign_map_redirect_is_not_followed_and_next_published_map_is_used(self):
        client=Mock(host='jobs.boeing.com')
        client.robots.site_maps.return_value=['https://jobs.boeing.com/old-map.xml','https://jobs.boeing.com/jobs.xml']
        client.get.side_effect=[ValueError('Unexpected source host or protocol'),(200,'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://jobs.boeing.com/job/test/role/185/12345</loc></url></urlset>')]
        self.assertEqual(len(c.discover(client)),1)
        self.assertEqual(len(client.discovery_warnings),1)

if __name__=='__main__':unittest.main()
