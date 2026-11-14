import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from collection_health import availability_failures
def report(*messages):return {'sources':{'synthetic':{'errors':[{'error':message} for message in messages]}}}
class CollectionHealthTests(unittest.TestCase):
    def test_only_explicit_upstream_service_errors_are_availability_warnings(self):
        self.assertEqual(len(availability_failures(report('Employer request failed: HTTP 503','Employer request failed: HTTP 521','Employer service unavailable: Workday outage redirect'))),3)
    def test_access_identity_and_mixed_failures_still_require_investigation(self):
        for error in ['Employer request failed: HTTP 403','Employer request failed: HTTP 429','Requisition identity changed','Crawler rules exclude requested URL','Reviewed discovery contains no individual job URLs']:
            self.assertIsNone(availability_failures(report('Employer request failed: HTTP 503',error)))
    def test_missing_diagnostics_cannot_hide_collector_crashes(self):
        self.assertIsNone(availability_failures({}));self.assertIsNone(availability_failures(report()))
