"""Bounded discovery from reviewed, public employer career listings."""

from datetime import datetime
import re
from urllib.parse import parse_qs, urljoin, urlsplit
from xml.etree import ElementTree

from employer_adapters import Document, text


FEEDS = {
    "jobs.intuit.com": (
        "/en/search-jobs",
        r"/(?:en/)?job/[^/]+/[^/]+/27595/(\d+)/?",
    ),
    "jobs.spectrum.com": (
        "/category/retail-jobs/4673/21675/1",
        r"/job/[^/]+/[^/]+/4673/(\d+)/?",
    ),
    "jobs.uber.com": (
        "/en/jobs/sitemap.xml",
        r"/en/jobs/(\d+)/?",
    ),
}


def role_id(url, host):
    """Match the exact reviewed employer posting route."""
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != host or parsed.query or parsed.fragment:
        return None
    match = re.fullmatch(FEEDS[host][1], parsed.path)
    return match[1] if match else None


def listing_links(body, listing_url):
    if listing_url.endswith(".xml"):
        root = ElementTree.fromstring(body)
        namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        if root.tag != namespace + "urlset":
            raise ValueError("Unexpected employer job sitemap format")
        return [entry.text for entry in root.findall(f"{namespace}url/{namespace}loc") if entry.text]

    return [
        urljoin(listing_url, node["attrs"]["href"])
        for node in Document(body).nodes
        if node["tag"] == "a" and node["attrs"].get("href")
    ]


def has_application(body, host, requisition):
    """Verify a requisition-specific employer application without visiting it."""
    if host == "jobs.uber.com":
        urls = re.findall(r'"applicationUrl"\s*:\s*"([^"\s]+)"',
                          body.replace(r'\"', '"'), re.IGNORECASE)
        expected = f"/hcmUI/CandidateExperience/en/sites/UberCareers/jobs/preview/{requisition}/apply/email"
        return any(
            target.scheme == "https" and target.netloc == "iaziqy.fa.ocs.oraclecloud.com"
            and target.path == expected
            for target in map(urlsplit, urls)
        )

    links = [
        urlsplit(node["attrs"].get("href", ""))
        for node in Document(body).nodes
        if node["tag"] == "a" and "job-apply" in node["attrs"].get("class", "").split()
    ]
    if host == "jobs.intuit.com":
        return any(
            target.scheme == "https" and target.netloc == "intuit.avature.net"
            and target.path == "/externalCareers/JobApplication"
            and parse_qs(target.query).get("pipelineId") == [requisition]
            for target in links
        )

    req = re.fullmatch(r"\d{4}-(\d+)", requisition)
    return bool(req and any(
        target.scheme == "https" and target.netloc == "careers-charter.icims.com"
        and re.fullmatch(rf"/jobs/{req[1]}/[^/]+/job/login/?", target.path)
        for target in links
    ))


def spectrum_posting_date(body):
    """Read the role's labeled date, which can predate its structured date."""
    dates = set()
    for node in Document(body).nodes:
        if node["tag"] != "span" or "job-date" not in node["attrs"].get("class", "").split():
            continue
        match = re.fullmatch(r"Date posted\s+(\d{1,2}/\d{1,2}/\d{4})", text(node).strip())
        if match:
            dates.add(datetime.strptime(match[1], "%m/%d/%Y").date().isoformat())
    if len(dates) != 1:
        raise ValueError("Missing or conflicting labeled Spectrum posting date")
    return dates.pop()


def discover(client):
    url = f"https://{client.host}{FEEDS[client.host][0]}"
    status, body = client.get(url)
    if status != 200:
        raise ValueError("Employer public job listing unavailable")

    found = {}
    for candidate in listing_links(body, url):
        req = role_id(candidate, client.host)
        if req:
            found.setdefault(req, candidate)

    if not found:
        raise ValueError("Employer listing has no matching individual job URLs")

    # Job IDs prioritize the bounded sample. Only the role page supplies posting dates.
    client.discovery_dates = {}
    client.discovery_limited = True
    client.discovery_warnings = []
    return found
