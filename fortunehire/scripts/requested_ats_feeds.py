"""Read only the reviewed, employer-linked public ATS tenants."""

from datetime import date, datetime
import html
import json
import re
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from employer_adapters import Document, text


ASHBY = "jobs.ashbyhq.com"
GREENHOUSE = "job-boards.greenhouse.io"
GREENHOUSE_API = "boards-api.greenhouse.io"
BOARDS = {
    "anthropic": (GREENHOUSE, "anthropic", "Anthropic", "www.anthropic.com"),
    "openai": (ASHBY, "openai", "OpenAI", "openai.com"),
    "perplexity": (ASHBY, "Perplexity", "Perplexity", "www.perplexity.ai"),
}
HOSTS = {board[0] for board in BOARDS.values()}
ACTIVE_CAP = 40
UUID = r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}"
US_OFFICES = {
    "Austin": "TX", "Boston": "MA", "New York": "NY", "New York City": "NY",
    "Palo Alto": "CA", "San Francisco": "CA", "Seattle": "WA",
    "San Diego": "CA", "Chicago": "IL", "Los Angeles": "CA",
    "Washington": "DC", "Washington DC": "DC", "Washington D.C.": "DC",
}
US_HINTS = {*map(str.casefold, US_OFFICES), "us remote", "united states"}


def role(url):
    target = urlsplit(url)
    if target.scheme != "https" or target.query or target.fragment:
        return None
    for company, (host, board, _, _) in BOARDS.items():
        if target.netloc != host:
            continue
        parts = target.path.removeprefix("/").removesuffix("/").split("/")
        if host == GREENHOUSE and len(parts) == 3 and parts[:2] == [board, "jobs"]:
            if re.fullmatch(r"[0-9]+", parts[2]):
                return company, parts[2]
        if host == ASHBY and len(parts) == 2 and parts[0].casefold() == board.casefold():
            if re.fullmatch(UUID, parts[1]):
                return company, parts[1]
    return None


def original_date(value):
    try:
        moment = datetime.fromisoformat(value)
        if moment.tzinfo is not None:
            return moment.astimezone(ZoneInfo("America/New_York")).date().isoformat()
    except (TypeError, ValueError):
        pass
    return ""


def greenhouse_json(client, board, suffix=""):
    status, body = client.get(f"https://{GREENHOUSE_API}/v1/boards/{board}/jobs{suffix}")
    return status, json.loads(body) if status == 200 else None


def ashby_data(body, company):
    _, board, name, corporate = BOARDS[company]
    marker = re.search(r"window\.__appData\s*=\s*", body)
    if not marker:
        raise ValueError("Missing public Ashby page data")
    data, _ = json.JSONDecoder().raw_decode(body[marker.end():])
    organization = data.get("organization") or {}
    website = urlsplit(organization.get("publicWebsite") or "")
    if (organization.get("name") != name or organization.get("hostedJobsPageSlug") != board
            or website.scheme != "https" or website.netloc != corporate):
        raise ValueError("Unexpected Ashby employer tenant")
    return data


def discover(client, client_factory):
    company = client.ats_company
    host, board, _, _ = BOARDS[company]
    if client.host != host:
        raise ValueError("Unexpected employer ATS host")
    found, dates = {}, {}
    if host == GREENHOUSE:
        client.greenhouse_api = client_factory(GREENHOUSE_API)
        status, data = greenhouse_json(client.greenhouse_api, board)
        rows = data.get("jobs") if status == 200 else None
        if not isinstance(rows, list) or (data.get("meta") or {}).get("total") != len(rows):
            raise ValueError("Incomplete public Greenhouse job inventory")
        for row in rows:
            url = row.get("absolute_url", "")
            req = str(row.get("id", ""))
            posted = original_date(row.get("first_published"))
            if posted and row.get("internal_job_id") and role(url) == (company, req):
                found[req], dates[req] = url, posted
    else:
        status, body = client.get(f"https://{host}/{board}")
        if status != 200:
            raise ValueError("Ashby public board unavailable")
        rows = (ashby_data(body, company).get("jobBoard") or {}).get("jobPostings")
        if not isinstance(rows, list):
            raise ValueError("Missing public Ashby job inventory")
        for row in rows:
            req = row.get("id", "")
            locations = [row, *(row.get("secondaryLocations") or [])]
            if re.fullmatch(UUID, req) and any(
                str(location.get("locationName", "")).casefold() in US_HINTS for location in locations
            ):
                found[req] = f"https://{host}/{board}/{req}"
    if not found:
        raise ValueError("No verified employer job links in ATS inventory")
    client.discovery_dates = dates
    client.discovery_limited = True
    client.discovery_warnings = []
    return found


def greenhouse_source(body, row, company, req, url):
    _, board, name, _ = BOARDS[company]
    doc = Document(body)
    title = doc.find("h1")
    form = doc.find("form", id="application-form")
    title_text = " ".join(text(title).split()) if title else ""
    if (row.get("id") != int(req) or row.get("company_name") != name
            or role(row.get("absolute_url", "")) != (company, req)
            or not title_text or title_text != " ".join(str(row.get("title", "")).split())
            or not form or form["attrs"].get("action") != f"/{board}/jobs/{req}"):
        raise ValueError("Conflicting Greenhouse job identity or missing application")
    posted = original_date(row.get("first_published"))
    if not posted:
        raise ValueError("Missing first-published Greenhouse date")
    labels = re.split(r"[|;]", (row.get("location") or {}).get("name") or "")
    locations = []
    for label in labels:
        city, separator, state = label.strip().rpartition(",")
        if separator and US_OFFICES.get(city.strip()) == state.strip():
            locations.append({"address": {"addressCountry": "US", "addressRegion": state.strip(),
                                          "addressLocality": city.strip()}})
    source = {
        "@type": "JobPosting", "identifier": {"value": row.get("requisition_id") or req},
        "title": title_text, "url": url, "jobLocation": locations, "datePosted": posted,
        "description": html.unescape(row.get("content") or ""),
        "_adapter": "greenhouse-public-first-published",
    }
    if not row.get("requisition_id"):
        source["_identifierType"] = "posting-id"
    deadline = original_date(row.get("application_deadline"))
    if deadline:
        source["validThrough"] = deadline
    types = {item.get("value") for item in (row.get("metadata") or []) if item.get("name") == "Location Type"}
    if len(types) == 1:
        kind = {"On-Site":"ON_SITE", "Hybrid":"HYBRID", "Hybrid (Travel-Required)":"HYBRID",
                "Remote":"TELECOMMUTE"}.get(types.pop())
        if kind:
            source["jobLocationType"] = kind
    return source


def ashby_source(body, company, req, url):
    _, _, name, corporate = BOARDS[company]
    posting = (ashby_data(body, company).get("posting") or {})
    if (posting.get("id") == req and posting.get("isListed") is False
            and posting.get("isConfidential") is False):
        return None
    if (posting.get("id") != req or posting.get("isListed") is not True
            or posting.get("isConfidential") is not False):
        raise ValueError("Missing listed public Ashby posting")
    doc = Document(body)
    rows = []
    for node in doc.nodes:
        if node["tag"] == "script" and node["attrs"].get("type") == "application/ld+json":
            data = json.loads("".join(value for value in node["children"] if isinstance(value, str)))
            if isinstance(data, dict) and data.get("@type") == "JobPosting":
                rows.append(data)
    if len(rows) != 1:
        raise ValueError("Missing individual Ashby JobPosting")
    row = rows[0]
    org = row.get("hiringOrganization") or {}
    identifier = row.get("identifier") or {}
    if (identifier.get("value") != req or org.get("name") != name
            or urlsplit(org.get("sameAs", "")).netloc != corporate
            or " ".join(str(row.get("title", "")).split()) != " ".join(str(posting.get("title", "")).split())):
        raise ValueError("Conflicting Ashby posting identity")
    try:
        posted = date.fromisoformat(row.get("datePosted"))
    except (TypeError, ValueError) as error:
        raise ValueError("Missing employer JobPosting date") from error
    row.update(url=url, datePosted=posted.isoformat(), _identifierType="posting-id",
               _adapter="ashby-public-jobposting")
    if not row.get("jobLocationType"):
        kind = {"OnSite":"ON_SITE", "Hybrid":"HYBRID", "Remote":"TELECOMMUTE"}.get(posting.get("workplaceType"))
        if kind:
            row["jobLocationType"] = kind
    return row


def fetch(client, url, body):
    company, req = role(url) or (None, None)
    if not company or company != client.ats_company:
        raise ValueError("Unexpected individual employer ATS route")
    _, board, _, _ = BOARDS[company]
    if client.host == GREENHOUSE:
        status, row = greenhouse_json(client.greenhouse_api, board, f"/{req}")
        if status != 200:
            raise ValueError("Greenhouse role detail unavailable")
        source = greenhouse_source(body, row, company, req, url)
    else:
        source = ashby_source(body, company, req, url)
        if source is None:
            return 404, ""  # A matching posting explicitly marked unlisted.
        status, application = client.get(url.rstrip("/") + "/application")
        if status != 200:
            raise ValueError("Public Ashby application unavailable")
        posting = (ashby_data(application, company).get("posting") or {})
        if (posting.get("id") != req or posting.get("isListed") is not True
                or posting.get("isConfidential") is not False):
            raise ValueError("Conflicting Ashby application identity")
    return 200, '<script type="application/ld+json">' + json.dumps(source).replace("<", "\\u003c") + "</script>"
