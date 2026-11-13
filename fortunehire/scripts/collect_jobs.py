"""Bounded, first-party career-site pilot. Python standard library only."""
from __future__ import annotations

import argparse
import copy
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from datetime import datetime, timezone
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'boeing': ('jobs.boeing.com', 'Aerospace & Defense'),
    'citigroup': ('jobs.citi.com', 'Financials'),
    'unitedhealth-group': ('careers.unitedhealthgroup.com', 'Health Care'),
}
UA = 'FortuneHirePilot/0.1 (+https://fortunehire.netlify.app/)'
STATES = dict(zip(
    'AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split(),
    'Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|District of Columbia|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming'.split('|')))


def state_name(value):
    value = str(value or '').strip()
    return STATES.get(value.upper(), value if value in STATES.values() else None)


def safe_url(url, host):
    p = urllib.parse.urlsplit(url)
    if p.scheme != 'https' or p.netloc != host or p.username or p.password:
        raise ValueError('Unexpected source host or protocol')
    return urllib.parse.urlunsplit(('https', host, p.path, '', ''))


def job_url(url, host):
    url = safe_url(url, host)
    if not re.fullmatch(r'/job/[^/]+/[^/]+/\d+/\d+', urllib.parse.urlsplit(url).path):
        raise ValueError('Not an individual employer job URL')
    return url


class Page(HTMLParser):
    def __init__(self, body):
        super().__init__(convert_charrefs=True)
        self.scripts, self.parts, self.script, self.hidden = [], [], None, 0
        self.feed(body)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script':
            self.script = [] if attrs.get('type', '').lower() == 'application/ld+json' else None
        if tag in ('script', 'style'): self.hidden += 1
        if tag in ('p', 'div', 'li', 'br', 'h1', 'h2', 'h3', 'dt', 'dd'): self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag == 'script' and self.script is not None:
            self.scripts.append(''.join(self.script)); self.script = None
        if tag in ('script', 'style'): self.hidden = max(0, self.hidden - 1)
        if tag in ('p', 'div', 'li', 'h1', 'h2', 'h3', 'dt', 'dd'): self.parts.append('\n')

    def handle_data(self, data):
        if self.script is not None: self.script.append(data)
        if not self.hidden: self.parts.append(data)

    @property
    def text(self):
        return re.sub(r'[ \t\r\f\v]+', ' ', ''.join(self.parts))


def postings(value):
    if isinstance(value, list):
        for item in value: yield from postings(item)
    elif isinstance(value, dict):
        kind = value.get('@type', [])
        if kind == 'JobPosting' or isinstance(kind, list) and 'JobPosting' in kind:
            yield value
        yield from postings(value.get('@graph', []))


def as_list(value):
    return value if isinstance(value, list) else [value] if value else []


def date_only(value):
    try: return datetime.strptime(str(value)[:10], '%Y-%m-%d').date().isoformat()
    except ValueError: return None


def normalize_posting(body, url, company, now):
    """Only explicit evidence populates filters; uncertainty is preserved."""
    host, sector = SOURCES[company]
    url = job_url(url, host)
    page = Page(body)
    candidates = []
    for script in page.scripts:
        try: candidates.extend(postings(json.loads(script)))
        except (ValueError, TypeError): continue
    matched = [j for j in candidates if str(j.get('url', '')).rstrip('/') == url]
    if len(matched) != 1: raise ValueError('Missing or ambiguous matching JobPosting data')
    source = matched[0]
    title = html.unescape(str(source.get('title', ''))).strip()
    req = source.get('identifier', {})
    req = str(req.get('value', '') if isinstance(req, dict) else req).strip()
    if not title or not req: raise ValueError('Missing title or requisition')
    description = Page(str(source.get('description', ''))).text
    locations = []
    for loc in as_list(source.get('jobLocation')):
        address = loc.get('address', {}) if isinstance(loc, dict) else {}
        country = address.get('addressCountry', '')
        if isinstance(country, dict): country = country.get('name', '')
        state = state_name(address.get('addressRegion'))
        city = str(address.get('addressLocality', '')).strip()
        if str(country).upper() in ('US', 'USA', 'UNITED STATES', 'UNITED STATES OF AMERICA') and state and city:
            item = {'city': city, 'state': state}
            if item not in locations: locations.append(item)
    eligible = []
    for loc in as_list(source.get('applicantLocationRequirements')):
        if not isinstance(loc, dict): continue
        state = state_name(loc.get('name'))
        if state and state not in eligible: eligible.append(state)
    arrangement, arrangement_evidence = 'unknown', ''
    labeled = re.search(r'(?:Remote\s+Job|Job\s+Type|Workplace\s+Type|Role\s+Type)\s*:?\s*(Hybrid|On[- ]?site|Remote)\b', page.text, re.I)
    if labeled:
        arrangement = {'hybrid':'hybrid','onsite':'on-site','remote':'remote'}[re.sub(r'[- ]','',labeled[1].lower())]
        arrangement_evidence = labeled[0]
    elif source.get('jobLocationType') == 'TELECOMMUTE':
        arrangement, arrangement_evidence = 'remote', 'JobPosting.jobLocationType=TELECOMMUTE'
    else:
        onsite = re.search(r'This position is expected to be 100% on[- ]?site', description, re.I)
        if onsite: arrangement, arrangement_evidence = 'on-site', onsite[0]
        remote = re.search(r'You[\u2019\']ll enjoy the flexibility to work remotely\s*\*?\s*from anywhere within the U\.?S\.?', description, re.I)
        if remote: arrangement, arrangement_evidence = 'remote', remote[0]
    # A posted office address is not evidence of remote eligibility.
    if arrangement != 'remote': eligible = []
    if not locations and not eligible: return None
    travel, travel_evidence = None, ''
    no_travel = re.search(r'\b(?:Travel\s*(?:Required)?\s*:\s*(?:None|No|0%)|No travel (?:is )?required)\b', description, re.I)
    yes_travel = re.search(r'\bTravel\s*:\s*(?:Up to\s*)?([1-9]\d?(?:\.\d+)?|100)%[^\n]{0,100}', description, re.I)
    if no_travel: travel, travel_evidence = False, no_travel[0]
    elif yes_travel: travel, travel_evidence = True, yes_travel[0]
    employment = 'Not specified'
    raw_type = ' '.join(str(x) for x in as_list(source.get('employmentType'))).lower().replace('_','-')
    for pattern, value in [('full-time','Full-time'),('full time','Full-time'),('part-time','Part-time'),('part time','Part-time'),('contract','Contract'),('temporary','Temporary'),('intern','Internship')]:
        if pattern in raw_type: employment = value; break
    if employment == 'Not specified':
        labeled_type = re.search(r'Time\s+Type\s*:\s*(Full[- ]time|Part[- ]time)', page.text, re.I)
        if labeled_type: employment = 'Full-time' if labeled_type[1].lower().startswith('full') else 'Part-time'
    # Pay from descriptions can have location-specific ranges. Do not guess scope.
    salary, salary_evidence = None, ''
    base = source.get('baseSalary') or {}
    if not isinstance(base, dict): base = {}
    value = base.get('value') or {}
    if not isinstance(value, dict): value = {}
    period = {'YEAR':'year','HOUR':'hour'}.get(value.get('unitText')) if isinstance(value, dict) else None
    low, high = value.get('minValue'), value.get('maxValue')
    if base.get('currency') == 'USD' and period and all(isinstance(v,(float,int)) and not isinstance(v,bool) and v>0 for v in [low,high]) and high>=low and len({l['state'] for l in locations})==1:
        salary = {'min':low,'max':high,'period':period,'currency':'USD','scopeStates':[locations[0]['state']]}
        salary_evidence = 'JobPosting.baseSalary; single published state'
    today = now.astimezone(ZoneInfo('America/New_York')).date().isoformat()
    deadline = date_only(source.get('validThrough'))
    deadlines = [deadline] if deadline else []
    for match in re.finditer(r'(?:Applications for this position will be accepted until|Anticipated Posting Close Date\s*:)\s*([A-Za-z]+\.?)\s+(\d{1,2}),?\s+(\d{4})', description+'\n'+page.text, re.I):
        value = match[1].rstrip('.')+' '+match[2]+' '+match[3]
        for fmt in ('%B %d %Y','%b %d %Y'):
            try: deadlines.append(datetime.strptime(value,fmt).date().isoformat()); break
            except ValueError: pass
    deadline = min(deadlines) if deadlines else None
    posted = date_only(source.get('datePosted'))
    deadline_note = ''
    if deadline and posted and deadline<posted:
        deadline_note = 'Employer deadline '+deadline+' predates its posting date '+posted+'; deadline requires confirmation.'
        deadline = None
    key = re.sub(r'[^a-z0-9]+','-',req.lower()).strip('-')
    return {
        'id':company+'-'+key, 'companyId':company, 'requisitionId':req, 'title':title, 'url':url,
        'arrangement':arrangement, 'locations':locations,
        'remoteScope':'states' if eligible else 'unknown', 'eligibleStates':eligible,
        'locationNote':'; '.join(l['city']+', '+l['state'] for l in locations) or 'Employer specifies eligible states: '+', '.join(eligible),
        'employmentType':employment, 'salary':salary,
        'salaryNote':'Structured employer pay for the listed state.' if salary else 'Pay or geographic scope not verified automatically. See employer posting.',
        'travelRequired':travel, 'travelNote':travel_evidence or 'Travel not verified automatically.',
        'postedAt':posted, 'closesAt':deadline,
        'reviewedAt':today, 'status':'closed' if deadline and deadline<today else 'reviewed', 'sector':sector,
        'sourceNote':'Automatically checked against the official individual posting. Missing fields remain unknown; pilot coverage is limited.'+(' '+deadline_note if deadline_note else ''),
        'checkedAt':now.isoformat(), 'collectionMethod':'official-jobposting-jsonld',
        'sourceHash':hashlib.sha256(json.dumps({'structured':source,'arrangement':arrangement_evidence,'employmentType':employment,'deadline':deadline},sort_keys=True,ensure_ascii=False).encode()).hexdigest(),
        'evidence':{'arrangement':arrangement_evidence,'travel':travel_evidence,'salary':salary_evidence,'deadline':deadline_note},
    }


class SourceError(RuntimeError): pass


class RestrictedRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, host): self.host = host
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        safe_url(newurl, self.host)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class Client:
    def __init__(self, host, delay=1):
        self.host, self.delay, self.last = host, delay, 0
        self.opener = urllib.request.build_opener(RestrictedRedirect(host))
        self.robots = None
        status, body = self.get('https://'+host+'/robots.txt', check=False)
        if status == 404: body = ''
        elif status != 200: raise SourceError('Cannot establish crawler rules: HTTP '+str(status))
        self.robots = urllib.robotparser.RobotFileParser()
        self.robots.parse(body.splitlines())
        self.delay = max(delay, self.robots.crawl_delay(UA) or self.robots.crawl_delay('*') or 0)

    def get(self, url, check=True):
        safe_url(url, self.host)
        if check and not self.robots.can_fetch(UA, url): raise SourceError('Crawler rules exclude requested URL')
        time.sleep(max(0, self.last+self.delay-time.monotonic()))
        self.last = time.monotonic()
        req = urllib.request.Request(url, headers={'User-Agent':UA,'Accept':'text/html, application/xml;q=0.9, */*;q=0.8'})
        try:
            with self.opener.open(req, timeout=30) as response:
                raw = response.read(25_000_001)
                if len(raw)>25_000_000: raise SourceError('Response exceeds size limit')
                return response.status, raw.decode('utf-8-sig')
        except urllib.error.HTTPError as error:
            if error.code in (404,410): return error.code, ''
            raise SourceError('Employer request failed: HTTP '+str(error.code)) from error


def discover(client):
    status, body = client.get('https://'+client.host+'/sitemap.xml')
    if status != 200: raise SourceError('Job sitemap unavailable')
    root = ET.fromstring(body)
    ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    if root.tag != ns+'urlset': raise SourceError('Unexpected sitemap format; manual adapter review required')
    found = {}
    for entry in root.findall(ns+'url'):
        url = entry.findtext(ns+'loc') or ''
        if '/job/' not in url: continue
        url = job_url(url, client.host)
        found[url.rsplit('/',1)[-1]] = url
    if not found: raise SourceError('Sitemap contains no individual job URLs')
    return found


def reconcile(company, old_jobs, state, discovered, fetch, now, max_new=20, cap=100):
    """Never close by absence from a sitemap or partial crawl."""
    host = SOURCES[company][0]
    previous = [j for j in old_jobs if j['companyId']==company]
    by_id = {j['id']:copy.deepcopy(j) for j in previous}
    old_urls = {j['url'].rsplit('/',1)[-1]:j for j in previous}
    source_state = copy.deepcopy(state)
    rejected = source_state.setdefault('rejected', {})
    quarantined = {k:v for k,v in source_state.setdefault('quarantined',{}).items() if (now-datetime.fromisoformat(v)).total_seconds()<86400}
    source_state['quarantined']=quarantined
    missing = source_state.setdefault('missing', {})
    report = {'discovered':len(discovered),'checked':0,'added':0,'changed':0,'closed':0,'skipped':0,'warnings':[],'errors':[]}
    active = [j for j in previous if j['status']!='closed']
    # Existing records are checked even when sitemap discovery stops mentioning them.
    queue = [(discovered.get(k,j['url']),j) for k,j in old_urls.items() if j['status']!='closed']
    room = max(0, cap-len(active))
    candidates = [(k,u) for k,u in discovered.items() if k not in old_urls and k not in rejected and k not in quarantined]
    candidates.sort(key=lambda pair:int(pair[0]), reverse=True)
    reopen = [(discovered[k],j) for k,j in old_urls.items() if j['status']=='closed' and k in discovered]
    queue += (reopen+[(u,None) for k,u in candidates])[:min(max_new,room)]
    closures = []
    for url, old in queue:
        job_url(url,host)
        try:
            status, body = fetch(url)
            report['checked'] += 1
            if status in (404,410):
                if old:
                    first = missing.get(old['id'])
                    if first and (now-datetime.fromisoformat(first)).total_seconds()>=21600:
                        closures.append(old['id'])
                    elif not first: missing[old['id']] = now.isoformat()
                continue
            if status != 200: raise SourceError('Unexpected HTTP '+str(status))
            job = normalize_posting(body,url,company,now)
            if job is None:
                if old: raise ValueError('Previously published job no longer has verified US geography')
                rejected[url.rsplit('/',1)[-1]] = now.isoformat(); report['skipped'] += 1
                continue
            # Requisition identity is stable across title/slug changes.
            if old and old['requisitionId'] != job['requisitionId']: raise ValueError('Requisition identity changed')
            missing.pop(job['id'],None)
            existing = by_id.get(job['id'])
            if existing:
                if existing.get('sourceHash') != job['sourceHash']: report['changed'] += 1
            else: report['added'] += 1
            by_id[job['id']] = job
            if job['status']=='closed' and (not existing or existing['status']!='closed'): report['closed'] += 1
        except (ValueError,SourceError,urllib.error.URLError,TimeoutError) as error:
            if old is None and isinstance(error,ValueError):
                report['warnings'].append({'url':url,'error':'Candidate quarantined: '+str(error)[:180]})
                source_state.setdefault('quarantined',{})[url.rsplit('/',1)[-1]]=now.isoformat()
                continue
            report['errors'].append({'url':url,'error':str(error)[:200]})
            # Access denial/rate limiting stops this employer; no retries or bypass.
            if isinstance(error,SourceError): break
    # Refuse bulk closure signals; outages must not empty the board.
    if len(closures)>max(2,len(active)*0.25):
        report['errors'].append({'error':'Bulk closure guard: previous records retained'})
    else:
        for key in closures:
            by_id[key]['status']='closed'; by_id[key]['closedAt']=now.isoformat(); report['closed'] += 1
    # Retry out-of-scope locations after a week; retain no full descriptions.
    source_state['rejected'] = {k:v for k,v in rejected.items() if (now-datetime.fromisoformat(v)).days<7}
    source_state['missing'] = {k:v for k,v in missing.items() if k in by_id and by_id[k]['status']!='closed'}
    report['activeTracked'] = sum(j['status']!='closed' for j in by_id.values())
    return list(by_id.values()), source_state, report


def atomic_json(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    temp.replace(path)


def run(root=ROOT, now=None, max_new=20):
    now = now or datetime.now(timezone.utc)
    path = root/'public/data/jobs.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    state_path = root/'automation/state.json'
    state = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {}
    report = {'schemaVersion':1,'attemptedAt':now.isoformat(),'coverage':'Bounded pilot: at most 100 tracked active US postings per employer; up to 20 new candidates per employer per run. Not a complete feed.','sources':{}}
    jobs = data['jobs']
    successes = 0
    for company,(host,sector) in SOURCES.items():
        try:
            client = Client(host)
            discovered = discover(client)
            refreshed, source_state, result = reconcile(company,jobs,state.get(company,{}),discovered,client.get,now,max_new=max_new)
            jobs = [j for j in jobs if j['companyId']!=company]+refreshed
            state[company] = source_state
            if result['checked'] and not result['errors']:
                result['lastSuccessfulAt']=now.isoformat(); successes += 1
            else:
                result['lastSuccessfulAt']=data.get('automation',{}).get('sources',{}).get(company,{}).get('lastSuccessfulAt')
            report['sources'][company]=result
        except Exception as error:
            report['sources'][company]={'errors':[{'error':str(error)[:300]}],'lastSuccessfulAt':data.get('automation',{}).get('sources',{}).get(company,{}).get('lastSuccessfulAt')}
    data['jobs']=sorted(jobs,key=lambda j:j['id'])
    data['automation']=report
    data['method']='Official employer sitemap discovery and individual JobPosting checks; bounded three-employer pilot.'
    if successes: data['updatedAt']=now.astimezone(ZoneInfo('America/New_York')).date().isoformat()
    atomic_json(path,data)
    atomic_json(state_path,state)
    atomic_json(root/'public/data/collection-status.json',report)
    print(json.dumps(report,indent=2))
    return not any(s.get('errors') for s in report['sources'].values())


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--max-new',type=int,default=20)
    args=parser.parse_args()
    if not 0<=args.max_new<=20: parser.error('--max-new must be between 0 and 20')
    raise SystemExit(0 if run(args.root,max_new=args.max_new) else 1)

