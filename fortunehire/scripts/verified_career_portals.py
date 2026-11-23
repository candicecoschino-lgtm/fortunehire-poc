"""Bounded public collection for the GE Vernova and ServiceNow career portals."""

from datetime import date, datetime
import html
import json
import re
from urllib.parse import quote, urlencode, urljoin, urlsplit, urlunsplit
from xml.etree import ElementTree

from employer_adapters import Document, text


GE = "careers.gevernova.com"
SERVICENOW = "careers.servicenow.com"
HOSTS = {GE, SERVICENOW}
GE_SEARCH = "/jobs?" + urlencode({"filter[country][0]": "United States of America"})
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
PERSONAS = {
    "Flexible": "HYBRID",
    "Remote": "TELECOMMUTE",
    "Required in Office": "ON_SITE",
    "Flexible or Remote": None,
}
EMPLOYERS = {GE: "GE Vernova", SERVICENOW: "ServiceNow"}


def role_id(url, host):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != host or parsed.query or parsed.fragment:
        return None
    pattern = r"/[^/]+/job/(R[0-9]+)/?" if host == GE else r"/jobs/([0-9]+)/[^/]+/?"
    match = re.fullmatch(pattern, parsed.path)
    return match[1] if match else None


def discover(client):
    found, dates = {}, {}
    if client.host == GE:
        origin = "https://" + GE
        for suffix in ("", "&page_number=2"):
            url = origin + GE_SEARCH + suffix
            status, body = client.get(url)
            if status != 200:
                raise ValueError("GE Vernova public U.S. search unavailable")
            for node in Document(body).nodes:
                if node["tag"] != "a" or not node["attrs"].get("href"):
                    continue
                role_url = urljoin(url, node["attrs"]["href"])
                req = role_id(role_url, GE)
                if req:
                    parts = urlsplit(role_url)
                    encoded = quote(parts.path, safe="/%:@!$&'()*+,;=-._~")
                    found.setdefault(req, urlunsplit((parts.scheme, parts.netloc, encoded, "", "")))
    else:
        status, body = client.get("https://" + SERVICENOW + "/sitemap.xml")
        if status != 200:
            raise ValueError("ServiceNow role sitemap unavailable")
        sitemap = ElementTree.fromstring(body)
        if sitemap.tag != SITEMAP_NS + "urlset":
            raise ValueError("Unexpected ServiceNow role sitemap format")
        for entry in sitemap.findall(SITEMAP_NS + "url"):
            url = entry.findtext(SITEMAP_NS + "loc") or ""
            req = role_id(url, SERVICENOW)
            if req:
                found[req] = url
                dates[req] = entry.findtext(SITEMAP_NS + "lastmod") or ""
    if not found:
        raise ValueError("Public employer discovery returned no matching individual job URLs")
    client.discovery_dates = dates
    client.discovery_limited = True
    client.discovery_warnings = []
    return found


def role_schema(doc, host, req):
    matches = []
    for node in doc.nodes:
        if node["tag"] == "script" and node["attrs"].get("type") == "application/ld+json":
            try:
                source = json.loads("".join(p for p in node["children"] if isinstance(p, str)))
            except ValueError:
                continue
            if (isinstance(source, dict) and source.get("@type") == "JobPosting"
                    and role_id(source.get("url", ""), host) == req
                    and (source.get("hiringOrganization") or {}).get("name") == EMPLOYERS[host]):
                matches.append(source)
    if len(matches) != 1:
        raise ValueError("Missing unique matching employer JobPosting")
    return matches[0]


def application_verified(doc, host, req):
    for node in doc.nodes:
        if node["tag"] != "a" or not node["attrs"].get("href"):
            continue
        target = urlsplit(node["attrs"]["href"])
        if target.scheme != "https":
            continue
        if host == GE:
            if (target.netloc == "gevernova.wd5.myworkdayjobs.com"
                    and re.fullmatch(rf"/(?:en-US/)?Vernova_ExternalSite/job/(?:[^/]+/)*[^/]+_{req}(?:-[0-9]+)?/apply/?", target.path)):
                return True
        elif (target.netloc == "jobs.smartrecruiters.com"
              and re.fullmatch(rf"/ServiceNow/{req}-[^/]+/?", target.path)):
            return True
    return False


def ge_fields(source, doc, req):
    fields = {}
    for node in doc.nodes:
        if node["tag"] != "dl" or "summary-list-item" not in node["attrs"].get("class", "").split():
            continue
        name, separator, value = text(node).partition(":")
        if separator and value.strip():
            if fields.setdefault(name.strip(), value.strip()) != value.strip():
                raise ValueError("Conflicting GE Vernova role summary fields")
    identifier = source.get("identifier")
    if not isinstance(identifier, dict) or identifier.get("value") != req or fields.get("Job ID") != req:
        raise ValueError("GE Vernova requisition identity mismatch")
    declared = [date.fromisoformat(fields.get("Job Posting Start Date", ""))]
    description = html.unescape(source.get("description", ""))
    for label in re.findall(r"\bthis posting is expected to remain open for at least seven days "
                            r"after it was posted on ([A-Za-z]+\s+\d{1,2},\s+\d{4}|\d{1,2}/\d{1,2}/\d{4})",
                            description, re.I):
        fmt = "%m/%d/%Y" if "/" in label else "%B %d, %Y"
        declared.append(datetime.strptime(label, fmt).date())
    posted = min(declared)
    summer = re.search(r"\bintern(?:ship)?\b.{0,40}\bsummer\s+(\d{4})\b", source.get("title", ""), re.I)
    if summer and posted >= date(int(summer[1]), 10, 1):
        raise ValueError("GE Vernova internship title names a season before its posting date")
    source["datePosted"] = posted.isoformat()
    end_date = fields.get("Job Posting End Date")
    if end_date:
        source["validThrough"] = date.fromisoformat(end_date).isoformat()
    kind = {"Full Time": "FULL_TIME", "Part Time": "PART_TIME", "Intern": "INTERN"}.get(fields.get("Type"))
    if kind:
        structured = source.get("employmentType") or []
        structured = structured if isinstance(structured, list) else [structured]
        if structured and kind not in structured:
            raise ValueError("Conflicting GE Vernova employment type")
        source["employmentType"] = kind
    locations = source.get("jobLocation") or []
    locations = locations if isinstance(locations, list) else [locations]
    source["jobLocation"] = [
        loc for loc in locations if isinstance(loc, dict) and (loc.get("address") or {}).get("addressLocality") not in (
            None, "", "Unspecified", "Other", "Remote")
    ]
    if "Remote - United States" in {line.strip() for line in fields.get("Location(s)", "").splitlines()} and re.search(
        r"\bthis is a remote (?:position|role)\b", description, re.I
    ):
        source["jobLocationType"] = "TELECOMMUTE"
        source["applicantLocationRequirements"] = {"@type": "Country", "name": "United States"}


def servicenow_fields(source, doc):
    if not re.fullmatch(r"JB[0-9]+", str(source.get("identifier", ""))):
        raise ValueError("Missing ServiceNow employer requisition")
    date.fromisoformat(source.get("datePosted", ""))
    personas = {text(n).strip() for n in doc.nodes if n["tag"] == "li"
                and "list-inline-item" in n["attrs"].get("class", "").split()
                and text(n).strip() in PERSONAS}
    if personas:
        label = next(iter(personas)) if len(personas) == 1 else "Conflicting role personas"
        kind = PERSONAS.get(label)
        source["_verifiedWorksiteLabel"] = label
        source.pop("jobLocationType", None)
        if kind:
            source["jobLocationType"] = kind
        else:
            source["_ambiguousWorksite"] = label
    locations = source.get("jobLocation") or []
    for location in locations if isinstance(locations, list) else [locations]:
        address = (location.get("address") or {}) if isinstance(location, dict) else {}
        if str(address.get("addressRegion", "")).casefold() == "district of columbia":
            address["addressRegion"] = "DC"
    if isinstance(source.get("industry"), str):
        source["occupationalCategory"] = source["industry"]


def enrich(body, url, host):
    req = role_id(url, host)
    if not req:
        raise ValueError("Unexpected individual employer role URL")
    doc = Document(body)
    source = role_schema(doc, host, req)
    if not application_verified(doc, host, req):
        raise ValueError("Missing matching official application link")
    if host == GE:
        ge_fields(source, doc, req)
    else:
        servicenow_fields(source, doc)
    source["_adapter"] = "verified-employer-portal"
    return '<script type="application/ld+json">' + json.dumps(source).replace("<", "\\u003c") + "</script>"
