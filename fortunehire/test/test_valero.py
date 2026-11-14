"""Synthetic Taleo display fields; never used as published jobs."""
import sys,json,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from unittest.mock import Mock,patch
from datetime import datetime,timezone
from urllib.parse import quote
import collect_jobs as c
from employer_sources import public_search
URL='https://valero.taleo.net/careersection/2/jobdetail.ftl?job=2600ABC'
NOW=datetime(2026,11,14,15,tzinfo=timezone.utc)
def body(posted='Nov 9, 2026, 3:30:38 PM',req='2600ABC',location='US-TX-Test City'):
    fields=['no','contestnumber','title','description','qualification','primarylocation','postingdate','unpostingdate','no']
    values=['rdPager!$!123',req,'Synthetic operator','<p>This position is a full-time onsite role.</p>','Skills.',location,posted,'Nov 30, 2026, 9:59:00 PM','123']
    mapping='descRequisition: {_size: 1, _hlid: '+repr(['reqlistitem.'+f for f in fields])+'}'
    history='!|!'.join(['ftlx0','reset','descRequisition']+[quote(v) for v in values])
    return '<input id="initialHistory" value="'+history+'"><script>'+mapping+'</script><aside>Work Type: Remote</aside>'
class ValeroTests(unittest.TestCase):
    def test_query_identity_is_preserved_without_timezone_or_tracking(self):
        self.assertEqual(c.job_url(URL+'&tz=GMT-05%3A00','valero.taleo.net'),URL)
        self.assertEqual(c.posting_key(URL),'2600ABC')
        self.assertNotEqual(c.posting_key(URL),c.posting_key(URL.replace('2600ABC','2600DEF')))
        for url in [URL.replace('job=2600ABC','job='),URL+'&job=2600DEF',URL.replace('jobdetail','jobsearch'),URL.replace('valero.taleo.net','other.taleo.net')]:
            with self.assertRaises(ValueError):c.job_url(url,'valero.taleo.net')
    def test_display_mapping_verifies_date_location_and_requisition(self):
        with patch.dict(c.SOURCES,{'valero':('valero.taleo.net','Energy')}):
            j=c.normalize_posting(body(),URL,'valero',NOW)
            self.assertEqual(j['postedAt'],'2026-11-09');self.assertEqual(j['closesAt'],'2026-11-30')
            self.assertEqual(j['arrangement'],'on-site');self.assertEqual(j['locations'],[{'city':'Test City','state':'Texas'}])
            self.assertEqual(j['url'],URL);self.assertTrue(c.recent_posting(j,NOW))
            self.assertFalse(c.recent_posting(c.normalize_posting(body(posted='Oct 19, 2026, 3:30:38 PM'),URL,'valero',NOW),NOW))
            for invalid in [body(req='2600DEF'),body(posted='yesterday'),body().replace('_size: 1','_size: 2')]:
                with self.assertRaises(ValueError):c.normalize_posting(invalid,URL,'valero',NOW)
            self.assertIsNone(c.normalize_posting(body(location='US-UNKNOWN-Test City'),URL,'valero',NOW))
    def test_discovery_uses_only_individual_employer_linked_featured_jobs(self):
        client=Mock(host='valero.taleo.net');landing=Mock()
        landing.get.return_value=(200,'<a href="'+URL+'&amp;tz=GMT">Role</a><a href="https://other.taleo.net/careersection/2/jobdetail.ftl?job=2600DEF">Other employer</a><a href="https://valero.taleo.net/careersection/2/jobsearch.ftl">Search</a>')
        factory=Mock(return_value=landing)
        self.assertEqual(public_search(client,factory),{'2600ABC':URL})
        factory.assert_called_once_with('www.valero.com');self.assertTrue(client.discovery_limited)
if __name__=='__main__':unittest.main()
