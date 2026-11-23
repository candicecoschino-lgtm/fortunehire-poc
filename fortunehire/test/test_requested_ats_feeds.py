"""Synthetic verification fixtures for the public ATS sources."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import collect_jobs as collector
import requested_ats_feeds as ats
from employer_sources import public_fetch, public_search


NOW = datetime(2026, 11, 22, 20, tzinfo=timezone.utc)
ASHBY_ID = "916fa6f6-f441-43c6-9769-27e4bf0b2cc9"
GREENHOUSE_ROLE = "https://job-boards.greenhouse.io/anthropic/jobs/12345"
ASHBY_ROLE = f"https://jobs.ashbyhq.com/openai/{ASHBY_ID}"


def ashby_page(company, *, include_posting=True, **fields):
    _, board, name, corporate = ats.BOARDS[company]
    posting = {
        "id": ASHBY_ID, "title": "Synthetic role", "isListed": True,
        "isConfidential": False, "workplaceType": "Hybrid",
    }
    posting.update(fields)
    data = {
        "organization": {
            "name": name, "hostedJobsPageSlug": board, "publicWebsite": f"https://{corporate}/",
        },
        "jobBoard": {"jobPostings": [{"id": ASHBY_ID, "locationName": "San Francisco"}]},
        "posting": posting if include_posting else None,
    }
    schema = {
        "@type": "JobPosting", "title": " Synthetic role", "identifier": {"value": ASHBY_ID},
        "hiringOrganization": {"name": name, "sameAs": f"https://{corporate}/"},
        "datePosted": "2026-11-16", "employmentType": "FULL_TIME",
        "jobLocation": {"address": {
            "addressCountry": "US", "addressLocality": "San Francisco", "addressRegion": "CA",
        }},
    }
    return ('<script>window.__appData = ' + json.dumps(data) + ';</script>'
            '<script type="application/ld+json">' + json.dumps(schema) + '</script>')


def greenhouse_detail(**fields):
    detail = {
        "id": 12345, "company_name": "Anthropic", "absolute_url": GREENHOUSE_ROLE,
        "title": "Synthetic role", "first_published": "2026-11-17T03:15:00Z",
        "updated_at": "2026-11-22T09:15:00Z", "location": {"name": "San Francisco, CA | London, UK"},
        "internal_job_id": 7654, "requisition_id": "REQ-007", "metadata": [], "content": "",
    }
    detail.update(fields)
    return detail


class RequestedAtsFeedTests(TestCase):
    def test_ashby_checks_listed_identity_and_application_for_both_tenants(self):
        for company in ("openai", "perplexity"):
            with self.subTest(company=company):
                host, board, _, _ = ats.BOARDS[company]
                url = f"https://{host}/{board}/{ASHBY_ID}"
                client = Mock(host=host, ats_company=company)
                client.get.return_value = (200, ashby_page(company))
                self.assertEqual(public_search(client, Mock()), {ASHBY_ID: url})
                _, body = public_fetch(client, url, Mock())
                job = collector.normalize_posting(body, url, company, NOW)
                self.assertEqual((job["postedAt"], job["employmentType"], job["arrangement"]),
                                 ("2026-11-16", "Full-time", "hybrid"))
                self.assertEqual(job["requisitionId"], ASHBY_ID)
                client.get.side_effect = [
                    (200, ashby_page(company)),
                    (200, ashby_page(company, id="different")),
                ]
                with self.assertRaisesRegex(ValueError, "application identity"):
                    public_fetch(client, url, Mock())
                with self.assertRaisesRegex(ValueError, "listed public"):
                    ats.ashby_source(ashby_page(company, isConfidential=True), company, ASHBY_ID, url)

    def test_greenhouse_matches_verified_first_publication_and_role_form(self):
        row = greenhouse_detail()
        api = Mock()
        api.get.side_effect = [
            (200, json.dumps({"jobs": [row], "meta": {"total": 1}})),
            (200, json.dumps(row)),
        ]
        body = '<h1>Synthetic role</h1><form id="application-form" action="/anthropic/jobs/12345"></form>'
        client = Mock(host=ats.GREENHOUSE, ats_company="anthropic")
        client.get.return_value = (200, body)
        factory = Mock(return_value=api)
        self.assertEqual(public_search(client, factory), {"12345": GREENHOUSE_ROLE})
        factory.assert_called_once_with(ats.GREENHOUSE_API)
        status, normalized = public_fetch(client, GREENHOUSE_ROLE, factory)
        self.assertEqual(status, 200)
        jobs, _, report = collector.reconcile(
            "anthropic", [], {}, {"12345": GREENHOUSE_ROLE}, Mock(return_value=(200, normalized)), NOW)
        self.assertEqual(report["added"], 1)
        self.assertEqual(jobs[0]["postedAt"], "2026-11-16")
        self.assertEqual(jobs[0]["employmentType"], "Not specified")
        self.assertEqual(jobs[0]["arrangement"], "unknown")
        self.assertEqual(jobs[0]["locations"], [{"city": "San Francisco", "state": "California"}])
        with self.assertRaisesRegex(ValueError, "first-published"):
            ats.greenhouse_source(body, greenhouse_detail(first_published=None), "anthropic", "12345", GREENHOUSE_ROLE)
        with self.assertRaisesRegex(ValueError, "application"):
            ats.greenhouse_source(body.replace("/12345", "/54321"), row, "anthropic", "12345", GREENHOUSE_ROLE)

    def test_route_and_retention_guards(self):
        self.assertIsNone(ats.role(ASHBY_ROLE + "/application"))
        self.assertIsNone(ats.role(GREENHOUSE_ROLE.replace("anthropic", "other")))
        self.assertIsNone(ats.role(ASHBY_ROLE + "?session=1"))
        client = Mock(host=ats.ASHBY, ats_company="openai")
        client.get.return_value = (200, ashby_page("openai"))
        _, body = public_fetch(client, ASHBY_ROLE, Mock())
        old = collector.normalize_posting(body, ASHBY_ROLE, "openai", NOW)
        foreign = ASHBY_ROLE.replace("/openai/", "/Perplexity/")
        with self.assertRaisesRegex(ValueError, "tenant"):
            collector.normalize_posting(body, foreign, "openai", NOW)
        denied = Mock(side_effect=collector.SourceError("Employer request failed: HTTP 429"))
        jobs, _, report = collector.reconcile("openai", [old], {}, {}, denied, NOW)
        self.assertEqual(jobs, [old])
        self.assertEqual(len(report["errors"]), 1)
