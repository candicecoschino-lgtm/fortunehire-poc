"""Synthetic role and lifecycle checks for the reviewed employer listings."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
from unittest import TestCase
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import collect_jobs as collector
from employer_sources import public_fetch, public_search


NOW = datetime(2026, 11, 22, 20, tzinfo=timezone.utc)
EXAMPLES = (
    ("intuit", "jobs.intuit.com", "/en/search-jobs",
     "/en/job/test-city/test-engineer/27595/12345", "INT-1"),
    ("charter-communications", "jobs.spectrum.com", "/category/retail-jobs/4673/21675/1",
     "/job/test-city/test-specialist/4673/12345", "2026-1234"),
    ("uber-technologies", "jobs.uber.com", "/en/jobs/sitemap.xml",
     "/en/jobs/12345", "12345"),
)


def page(url, requisition, **fields):
    posting = {
        "@type": "JobPosting",
        "identifier": {"value": requisition},
        "url": url,
        "title": "Synthetic test role",
        "datePosted": "2026-11-20",
        "description": "<p>Organize the team’s project documents.</p>",
        "jobLocation": {"address": {
            "addressCountry": "US", "addressRegion": "CA", "addressLocality": "Test City"
        }},
    }
    visible = fields.pop("visible_date", None)
    application_req = fields.pop("application_req", requisition)
    posting.update(fields)
    body = '<script type="application/ld+json">' + json.dumps(posting) + '</script>'
    if url.startswith("https://jobs.spectrum.com/"):
        if visible is None:
            visible = datetime.fromisoformat(posting["datePosted"]).strftime("%m/%d/%Y")
        body += f'<span class="job-date job-info">Date posted {visible}</span>'
        body += (f'<a class="job-apply" href="https://careers-charter.icims.com/jobs/'
                 f'{application_req.split("-")[-1]}/test-role/job/login">Apply</a>')
    elif url.startswith("https://jobs.intuit.com/"):
        body += (f'<a class="job-apply" href="https://intuit.avature.net/externalCareers/'
                 f'JobApplication?pipelineId={application_req}">Apply</a>')
    else:
        application = ('https://iaziqy.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/'
                       f'UberCareers/jobs/preview/{application_req}/apply/email?mode=location')
        body += '<script>' + json.dumps(json.dumps({"ApplicationUrl": application})) + '</script>'
    return body


class PublicListingFeedTests(TestCase):
    def test_uses_only_reviewed_listing_and_deduplicates_individual_links(self):
        for company, host, listing, path, _ in EXAMPLES:
            with self.subTest(company=company):
                origin = "https://" + host
                role = origin + path
                foreign = "https://example.org" + path
                if listing.endswith(".xml"):
                    listing_body = (
                        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                        + "".join(f"<url><loc>{link}</loc><lastmod>2026-11-22</lastmod></url>"
                                  for link in (role, role + "/", foreign, origin + "/en/jobs/"))
                        + "</urlset>"
                    )
                else:
                    listing_body = "".join(f'<a href="{link}">Role</a>'
                                           for link in (path, role + "/", foreign, role + "?unreviewed=1"))
                client = Mock(host=host)
                client.get.return_value = (200, listing_body)
                self.assertEqual(public_search(client, Mock()), {"12345": role})
                self.assertEqual(client.discovery_dates, {})
                client.get.assert_called_once_with(origin + listing)
                with self.assertRaises(ValueError):
                    collector.job_url(role + "?unreviewed=1", host)

    def test_verified_roles_preserve_source_fields_and_unknowns_on_repeat(self):
        for company, host, _, path, requisition in EXAMPLES:
            with self.subTest(company=company):
                url = "https://" + host + path
                client = Mock(host=host)
                client.get.return_value = (200, page(url, requisition))
                fetch = lambda target: public_fetch(client, target, Mock())
                first, state, report = collector.reconcile(company, [], {}, {"12345": url}, fetch, NOW)
                self.assertEqual(report["added"], 1)
                job = first[0]
                self.assertEqual((job["url"], job["requisitionId"], job["postedAt"]),
                                 (url, requisition, "2026-11-20"))
                self.assertEqual(job["locations"], [{"city": "Test City", "state": "California"}])
                self.assertEqual(job["employmentType"], "Not specified")
                self.assertEqual(job["arrangement"], "unknown")
                client.get.return_value = (200, page(url, requisition, employmentType="PART_TIME"))
                second, state, report = collector.reconcile(company, first, state, {}, fetch, NOW,
                                                            max_new=0)
                self.assertEqual(report["added"], 0)
                self.assertEqual(report["changed"], 1)
                self.assertEqual(len(second), 1)
                self.assertEqual((second[0]["id"], second[0]["employmentType"]), (job["id"], "Part-time"))

    def test_lifecycle_retains_existing_rows_on_denial_and_requires_repeat_missing(self):
        for company, host, _, path, requisition in EXAMPLES:
            with self.subTest(company=company):
                url = "https://" + host + path
                old = collector.normalize_posting(page(url, requisition), url, company, NOW)
                denied = Mock(side_effect=collector.SourceError("Employer request failed: HTTP 429"))
                kept, state, report = collector.reconcile(company, [old], {}, {}, denied, NOW)
                self.assertEqual(kept, [old])
                self.assertEqual(len(report["errors"]), 1)
                denied.assert_called_once_with(url)
                gone = Mock(return_value=(404, ""))
                kept, state, report = collector.reconcile(company, kept, state, {}, gone, NOW)
                self.assertEqual(kept, [old])
                self.assertEqual(report["pendingClosureChecks"], 1)
                closed, _, report = collector.reconcile(company, kept, state, {}, gone,
                                                        NOW + timedelta(hours=7))
                self.assertEqual(closed[0]["status"], "closed")
                self.assertEqual(report["closed"], 1)

    def test_spectrum_uses_earlier_dated_employer_evidence_and_rejects_missing_label(self):
        company, host, _, path, req = EXAMPLES[1]
        url = "https://" + host + path
        body = page(url, req, visible_date="08/05/2026")
        job = collector.normalize_posting(body, url, company, NOW)
        self.assertEqual(job["postedAt"], "2026-08-05")
        jobs, _, report = collector.reconcile(company, [], {}, {"12345": url},
                                               Mock(return_value=(200, body)), NOW)
        self.assertFalse(jobs)
        self.assertEqual(report["outsidePostingWindow"], 1)
        with self.assertRaisesRegex(ValueError, "posting date"):
            collector.normalize_posting(page(url, req, visible_date=""), url, company, NOW)

    def test_cross_role_metadata_wrong_geography_and_stale_postings_are_excluded(self):
        for company, host, _, path, requisition in EXAMPLES:
            with self.subTest(company=company):
                url = "https://" + host + path
                other = url.replace("12345", "67890")
                with self.assertRaises(ValueError):
                    collector.normalize_posting(page(other, requisition), url, company, NOW)
                with self.assertRaisesRegex(ValueError, "application"):
                    collector.normalize_posting(page(url, requisition, application_req="9-99999"),
                                                url, company, NOW)
                foreign = page(url, requisition, jobLocation={"address": {
                    "addressCountry": "CA", "addressRegion": "Ontario", "addressLocality": "Toronto"
                }})
                self.assertIsNone(collector.normalize_posting(foreign, url, company, NOW))
                stale = Mock(return_value=(200, page(url, requisition, datePosted="2026-09-01")))
                jobs, _, report = collector.reconcile(company, [], {}, {"12345": url}, stale, NOW)
                self.assertFalse(jobs)
                self.assertEqual(report["outsidePostingWindow"], 1)
        url = "https://jobs.uber.com/en/jobs/12345"
        with self.assertRaisesRegex(ValueError, "requisition"):
            collector.normalize_posting(page(url, "67890"), url, "uber-technologies", NOW)
