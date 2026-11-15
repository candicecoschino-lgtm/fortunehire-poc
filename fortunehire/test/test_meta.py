import sys,json,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import collect_jobs as c
from meta_public import discover,enrich,role_id,SITEMAP
URL='https://www.metacareers.com/profile/job_details/12345/'
def fixture(date='2026-11-14',record_id='12345'):
 source={'@type':'JobPosting','title':'Synthetic Meta engineer','identifier':{'value':'REQ123'},'datePosted':date,'description':'Role duties.','responsibilities':'Travel: 25%.','qualifications':'Relevant skills.','hiringOrganization':{'name':'Meta'},'employmentType':'FULL_TIME','jobLocation':{'address':{'addressCountry':'US','addressRegion':'WA','addressLocality':'Seattle'}}}
 record={'xcp_requisition_job_description':{'id':record_id,'title':source['title'],'public_compensation':[{'country_code':'US','compensation_amount_minimum':'$80,000/year','compensation_amount_maximum':'$100,000/year'},{'country_code':'CA','compensation_amount_minimum':'$900,000/year','compensation_amount_maximum':'$999,999/year'}],'internal_departments':['DO NOT PUBLISH']}}
 return '<link rel="canonical" href="'+URL+'"><script type="application/ld+json">'+json.dumps(source)+'</script><script type="application/json">'+json.dumps(record)+'</script><aside>Work Type: Remote</aside>'
class MetaTests(unittest.TestCase):
 def test_url_requires_official_numeric_individual_route(self):
  self.assertEqual(role_id(URL),'12345')
  for u in [URL+'?other=1',URL+'#private',URL.replace('www.metacareers.com','other.example'),URL.replace('12345','search')]:
   self.assertIsNone(role_id(u))
   with self.assertRaises(ValueError):c.job_url(u,'www.metacareers.com')
 def test_only_advertised_job_sitemap_is_used_and_lastmod_is_not_post_date(self):
  client=Mock(host='www.metacareers.com');client.robots.site_maps.return_value=[SITEMAP]
  client.get.return_value=(200,'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>'+URL+'</loc><lastmod>2099-01-01</lastmod></url><url><loc>https://other.example/profile/job_details/456/</loc></url></urlset>')
  self.assertEqual(discover(client),{'12345':URL});self.assertEqual(client.discovery_dates,{});client.get.assert_called_once_with(SITEMAP)
  client.robots.site_maps.return_value=[]
  with self.assertRaises(ValueError):discover(client)
 def test_identity_and_description_scope_pay_country_and_original_date(self):
  with patch.dict(c.SOURCES,{'meta':('www.metacareers.com','Technology')}):
   now=datetime(2026,11,15,tzinfo=timezone.utc);j=c.normalize_posting(fixture(),URL,'meta',now)
   self.assertEqual(j['arrangement'],'unknown');self.assertEqual(j['employmentType'],'Full-time');self.assertEqual(j['travelRequired'],True);self.assertIsNone(j['salary']);self.assertIn('$80,000/year',j['publishedPay']['text']);self.assertNotIn('900,000',j['publishedPay']['text']);self.assertNotIn('DO NOT PUBLISH',json.dumps(j));self.assertEqual(j['postedAt'],'2026-11-14')
   self.assertFalse(c.recent_posting(c.normalize_posting(fixture('2025-01-01'),URL,'meta',now),now))
   with self.assertRaisesRegex(ValueError,'identity|details'):c.normalize_posting(fixture(record_id='999'),URL,'meta',now)
