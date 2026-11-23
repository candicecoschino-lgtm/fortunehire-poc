"""Synthetic evidence and lifecycle checks for both official career portals."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
from unittest import TestCase
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import collect_jobs as collector
from employer_sources import public_fetch, public_search
import verified_career_portals as portals


NOW = datetime(2026, 11, 22, 20, tzinfo=timezone.utc)
GE = "https://careers.gevernova.com/test-role/job/R1234567"
SN = "https://careers.servicenow.com/jobs/744000162883203/test-role/"


def schema(host, url, **changes):
    row = {
        "@type": "JobPosting",
        "url": url,
        "hiringOrganization": {"name": portals.EMPLOYERS[host]},
        "identifier": {"value": "R1234567"} if host == portals.GE else "JB0077336",
        "title": "Synthetic test role",
        "datePosted": "2026-11-20T05:41:49+00:00" if host == portals.GE else "2026-11-19",
        "employmentType": "FULL_TIME",
        "description": "<p>Role-specific duties are supplied by the employer.</p>",
        "jobLocation": {"address": {"addressCountry": "US", "addressLocality": "Atlanta",
                                     "addressRegion": "GA"}},
    }
    row.update(changes)
    return '<script type="application/ld+json">' + json.dumps(row) + '</script>'


def summary(**values):
    return "".join(f'<dl class="summary-list-item"><dt>{label}:</dt><dd>{value}</dd></dl>'
                   for label, value in values.items())


class VerifiedCareerPortalTests(TestCase):
    def test_ge_discovers_only_roles_from_filtered_search(self):
        client = Mock(host=portals.GE)
        client.get.return_value = (200, f'<a href="{GE}">Role</a><a href="/jobs/page/2">Next</a>')
        self.assertEqual(public_search(client, Mock()), {"R1234567": GE})
        self.assertEqual([x.args[0] for x in client.get.call_args_list], [
            "https://" + portals.GE + portals.GE_SEARCH,
            "https://" + portals.GE + portals.GE_SEARCH + "&page_number=2",
        ])

    def test_ge_uses_labeled_start_deadline_type_and_removes_fake_city(self):
        role = schema(portals.GE, GE, description="This is a remote position. This posting is expected to remain open for at least seven days after it was posted on 11/17/2026.", jobLocation=[
            {"address": {"addressCountry": "US", "addressLocality": "Unspecified", "addressRegion": "SC"}},
            {"address": {"addressCountry": "US", "addressLocality": "Boston", "addressRegion": "MA"}},
        ])
        role += summary(**{"Job ID": "R1234567", "Type": "Full Time", "Job Posting Start Date": "2026-11-19",
                          "Job Posting End Date": "2026-11-23", "Location(s)": "Remote - United States"})
        role += '<a href="https://gevernova.wd5.myworkdayjobs.com/Vernova_ExternalSite/job/Remote/Test_R1234567-2/apply">Apply</a>'
        client = Mock(host=portals.GE)
        client.get.return_value = (200, role)
        _, body = public_fetch(client, GE, Mock())
        job = collector.normalize_posting(body, GE, "ge-vernova", NOW)
        self.assertEqual((job["postedAt"], job["closesAt"], job["employmentType"]),
                         ("2026-11-17", "2026-11-23", "Full-time"))
        self.assertEqual(job["locations"], [{"city": "Boston", "state": "Massachusetts"}])
        self.assertEqual((job["arrangement"], job["remoteScope"]), ("remote", "nationwide"))
        self.assertEqual(collector.normalize_posting(body, GE, "ge-vernova", NOW+timedelta(days=2))["status"],
                         "closed")
        client.get.return_value = (200, role.replace("_R1234567-2", "_R1234568-2"))
        with self.assertRaisesRegex(ValueError, "application"):
            public_fetch(client, GE, Mock())

    def test_ge_quarantines_internship_whose_advertised_season_has_passed(self):
        body = schema(portals.GE, GE, title="Facility Maintenance Internship Summer 2026")
        body += summary(**{"Job ID": "R1234567", "Job Posting Start Date": "2026-11-20"})
        body += '<a href="https://gevernova.wd5.myworkdayjobs.com/Vernova_ExternalSite/job/Test_R1234567/apply">Apply</a>'
        with self.assertRaisesRegex(ValueError, "season before"):
            portals.enrich(body, GE, portals.GE)

    def test_servicenow_uses_individual_persona_not_boilerplate_or_search_date(self):
        client = Mock(host=portals.SERVICENOW)
        sitemap = ('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                   f'<url><loc>{SN}</loc><lastmod>2026-11-22</lastmod></url></urlset>')
        client.get.return_value = (200, sitemap)
        self.assertEqual(public_search(client, Mock()), {"744000162883203": SN})
        for persona, expected in (("Flexible", "hybrid"), ("Remote", "remote"),
                                  ("Required in Office", "on-site"), ("Flexible or Remote", "unknown")):
            with self.subTest(persona=persona):
                role = schema(portals.SERVICENOW, SN, jobLocationType="TELECOMMUTE", industry="Software Engineering")
                role += f'<li class="list-inline-item">{persona}</li>'
                role += '<a href="https://jobs.smartrecruiters.com/ServiceNow/744000162883203-test-role?oga=true">Apply</a>'
                client.get.return_value = (200, role)
                _, body = public_fetch(client, SN, Mock())
                job = collector.normalize_posting(body, SN, "servicenow", NOW)
                self.assertEqual((job["postedAt"], job["arrangement"]), ("2026-11-19", expected))
                self.assertEqual(job["functionContext"]["category"], "Software Engineering")
                if expected == "unknown":
                    self.assertTrue(job["arrangementReviewRequired"])
                    self.assertIn("Flexible or Remote", job["evidence"]["arrangement"])

    def test_access_failure_retains_existing_role(self):
        raw = schema(portals.SERVICENOW, SN)
        role = collector.normalize_posting(raw, SN, "servicenow", NOW)
        denied = Mock(side_effect=collector.SourceError("Employer request failed: HTTP 403"))
        rows, _, report = collector.reconcile("servicenow", [role], {}, {}, denied, NOW)
        self.assertEqual(rows, [role])
        self.assertEqual(len(report["errors"]), 1)
