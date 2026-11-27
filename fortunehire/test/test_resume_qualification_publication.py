import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_resume_qualifications import matching_records, qualification_record
from collect_jobs import posting_key, reconcile


class ResumeQualificationPublicationTests(unittest.TestCase):
    def test_amazon_refresh_captures_qualifications_without_changing_search_records(self):
        url = 'https://www.amazon.jobs/en/jobs/12345/software-engineer'
        now = datetime(2026, 11, 27, tzinfo=timezone.utc)
        body = json.dumps({
            'pageTitle': 'Software Engineer',
            'pageUrl': url,
            'pageDescription': 'Basic Qualifications\n- Experience building data pipelines.\n'
                               'Preferred Qualifications\n- Python experience.',
            'amazonPosting': {'id_icims': '12345', 'title': 'Software Engineer',
                              'posted_date': 'November 25, 2026', 'locations': [],
                              'country_code': 'US', 'state': 'WA', 'city': 'Seattle'},
        })
        captured = {}

        def capture(job, source, verified_body):
            captured[job['id']] = qualification_record(job, source, verified_body)

        args = ('amazon', [], {}, {posting_key(url): url}, lambda _: (200, body), now)
        plain = reconcile(*args)
        joined = reconcile(*args, capture_qualification=capture)
        self.assertEqual(plain, joined)
        records = matching_records(joined[0], captured)
        self.assertEqual(set(records), {'amazon-12345'})
        self.assertEqual([(row['kind'], row['text']) for row in records['amazon-12345']['evidence']], [
            ('required', 'Experience building data pipelines.'),
            ('preferred', 'Python experience.'),
        ])
        self.assertEqual(matching_records([{**joined[0][0], 'sourceHash': 'changed'}], captured), {})
