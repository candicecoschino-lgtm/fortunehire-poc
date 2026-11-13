"""Bounded, first-party career-site pilot. Python standard library only."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import copy
import hashlib
import http.client
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
from employer_adapters import extract as extract_employer_page, Document
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
REGISTRY=json.loads((ROOT/'public/data/job-sources.json').read_text(encoding='utf-8'))
SOURCES={key:(value['host'],value['sector']) for key,value in REGISTRY['sources'].items()}
UA = 'FortuneHirePilot/0.1 (+https://fortunehire.netlify.app/)'
POSTING_MAX_AGE_DAYS = 14
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
    return urllib.parse.urlunsplit(('https', host, urllib.parse.quote(p.path,safe='/%:@!$&\'()*+,;=-._~'), '', ''))


def job_url(url, host):
    url = safe_url(url, host)
    if not re.search(r'/jobs?/[^/]+|/search/jobdetails/[^/]+/[0-9a-fA-F-]{36}$|/en-us/job-detail/[^/]+',urllib.parse.urlsplit(url).path.rstrip('/')) or len(url)>2000:
        raise ValueError('Not an individual employer job URL')
    return url


def posting_key(url):
    path=urllib.parse.urlsplit(url).path
    if urllib.parse.urlsplit(url).hostname.endswith('.myworkdayjobs.com') and '/job/' in path:
        req=path.rstrip('/').rsplit('_',1)[-1]
        if re.fullmatch(r'(?:JR\d+|R-\d+)-\d+',req,re.I):req=req.rsplit('-',1)[0]
        return req
    if '/search/jobdetails/' in path:return path.rstrip('/').rsplit('/',1)[-1]
    if '/en-us/job-detail/' in path:return path.split('/en-us/job-detail/',1)[1].split('/')[0]
    tail=re.split(r'/jobs?/',urllib.parse.urlsplit(url).path,maxsplit=1)[-1].strip('/').split('/')
    cisco=re.fullmatch(r'CISCISGLOBAL(\d+)EXTERNAL[A-Z]+',tail[0],re.I)
    if cisco:return cisco[1]
    if re.fullmatch(r'w\d+',tail[0],re.I): return '/'.join(tail)
    if len(tail)>=4 and tail[-1].isdigit() and tail[-2].isdigit(): return tail[-1]
    return re.sub(r'__[a-z]{2}(?:-[a-z]{2})?$','',tail[0],flags=re.I)


def discovery_priority(key):
    # Only a discovery preference; the actual employer date controls eligibility.
    if re.fullmatch(r'[0-9A-Fa-f]{24,}',key): return (0,key)
    if re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}',key): return (0,'')
    digits=re.findall(r'\d+',key)
    return (1,int(digits[-1])) if digits else (0,key)


def language_priority(url):
    path=urllib.parse.urlsplit(url).path
    if re.search(r'/(?:us|global)/en/',path): return 4
    if path.startswith(('/en/','/en-us/')): return 3
    if re.match(r'/[a-z]{2}(?:-[a-z]{2})?/',path): return 0
    return 2


class Page(HTMLParser):
    def __init__(self, body):
        super().__init__(convert_charrefs=True)
        self.scripts, self.parts, self.script, self.hidden = [], [], None, 0
        self.canonical=None
        self.feed(body)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag=='link' and attrs.get('rel','').lower()=='canonical': self.canonical=attrs.get('href')
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


def recent_posting(job, now):
    posted=date_only(job.get('postedAt'))
    if not posted: return False
    today=now.astimezone(ZoneInfo('America/New_York')).date()
    age=(today-datetime.strptime(posted,'%Y-%m-%d').date()).days
    return 0<=age<=POSTING_MAX_AGE_DAYS


MONEY = r'\$\s*\d[\d,]*(?:\.\d{1,2})?'
PAY_UNIT = r'(?:\s*(?:/\s*(?:hr|hour|yr|year)|per\s+(?:hour|year))\.?)?'
PAY_RANGE = re.compile('('+MONEY+')'+PAY_UNIT+r'\s*(?:[-\u2013\u2014]|to)\s*('+MONEY+')'+PAY_UNIT, re.I)


def extract_published_pay(description, locations, company, nationwide=False):
    """Preserve published ranges even when period/scope cannot support filtering."""
    states = sorted({loc['state'] for loc in locations})
    lines = [re.sub(r'\s+',' ',line).strip() for line in description.splitlines() if line.strip()]
    flat = ' '.join(lines)
    if company == 'citigroup':
        primary = re.search(r'Primary Location\s*:\s*([^\n]+)',description,re.I)
        primary_states = [s for s in sorted(STATES.values(),key=len,reverse=True) if primary and re.search(r'\b'+re.escape(s)+r'\b',primary[1],re.I)]
        scoped = [s for s in primary_states if s in states]
        if not scoped and primary:
            scoped=sorted({loc['state'] for loc in locations if re.search(r'\b'+re.escape(loc['city'])+r'\b',primary[1],re.I)})
        bands = re.findall(r'Primary Location Full Time Salary Range\s*:\s*('+MONEY+r'\s*[-\u2013\u2014]\s*'+MONEY+')',flat,re.I)
        bands = list(dict.fromkeys(bands))
        if bands and len(scoped)==1:
            # This label does not explicitly state the period. Display verbatim;
            # do not invent an hourly/annual value for the numerical pay filter.
            return None, {'text':'Primary-location salary range: '+'; '.join(bands),'scopeStates':scoped,'note':'Employer range for '+scoped[0]+'. Other locations may differ. Pay period is not specified in this label.'}
    evidence = []
    for i,line in enumerate(lines):
        if re.search(r'\b(?:summary pay range|(?:annual|hourly) pay for this role|(?:salary|pay)(?: range)? for (?:this|the) (?:role|position))\b',line,re.I) or company=='centene' and re.match(r'^Pay Range:\s*\$',line,re.I):
            context = line
            if not PAY_RANGE.search(context) and i+1<len(lines): context += ' '+lines[i+1]
            if PAY_RANGE.search(context): evidence.append(context)
    evidence = list(dict.fromkeys(evidence))
    if not evidence:
        # Keep published bands visible even when period or geography cannot
        # safely drive a numeric filter. Never turn target cash into base pay.
        displayed=[]
        for i,line in enumerate(lines):
            if not re.search(r'\b(?:pay|salary|compensation|earn)\b',line,re.I): continue
            context=line
            if not re.search(r'\$\s*\d|\d[\d,]*(?:\.\d+)?\s+USD\b',context) and i+1<len(lines): context+=' '+lines[i+1]
            if re.search(r'\$\s*\d|\d[\d,]*(?:\.\d+)?\s+USD\b',context):
                if len(context)>800:
                    for money in re.finditer(r'\$\s*\d[\d,.]*|\d[\d,]*(?:\.\d+)?\s+USD\b',context):
                        prefix=context[max(0,money.start()-140):money.start()]
                        anchors=list(re.finditer(r'\b(?:pay|salary|compensation|earn)\b',prefix,re.I))
                        if anchors:
                            start=max(0,money.start()-140)+anchors[-1].start()
                            displayed.append(context[start:money.start()+400]);break
                else:displayed.append(context)
        if displayed:
            return None,{'text':' | '.join(dict.fromkeys(displayed))[:1000],'scopeStates':states,'note':'Employer-published pay text. Period, pay components, or location-specific bands require confirmation; this text is not used for numeric pay filtering.'}
        return None,None
    records=[]
    for text in evidence:
        hourly=bool(re.search(r'\b(?:hourly|per hour|an hour)\b|/\s*(?:hr|hour)\b',text,re.I))
        annual=bool(re.search(r'\b(?:annual|annually|per year|per annum|a year)\b|/\s*(?:yr|year)\b',text,re.I))
        period='hour' if hourly and not annual else 'year' if annual and not hourly else None
        for match in PAY_RANGE.finditer(text):
            low, high = [float(re.sub(r'[$,\s]','',v)) for v in match.groups()]
            if not 0<low<=high: continue
            suffix = ' / hour' if period=='hour' else ' / year' if period=='year' else ''
            if re.search(r'/\s*(?:hr|hour|yr|year)\b|per\s+(?:hour|year)',match[0],re.I): suffix=''
            anchors=list(re.finditer(r'\b(?:Summary pay range|(?:annual|hourly) pay for this role|(?:salary|pay)(?: range)? for (?:this|the) (?:role|position))\b',text[:match.start()],re.I))
            start=anchors[-1].start() if anchors else match.start()
            label = text[start:match.start()].strip()[-100:]
            records.append((low,high,period,(label+' '+match[0]+suffix).strip()))
    if not records: return None,None
    unique = {(low,high,period) for low,high,period,text in records}
    published={'text':' | '.join(dict.fromkeys(r[3] for r in records))[:1000],'scopeStates':states,'note':'Employer-published range for listed locations; pay may vary by level or location.'}
    salary=None
    if len(unique)==1:
        low,high,period=next(iter(unique))
        # Explicit state-specific qualifiers need manual scope review. A generic
        # role-wide statement can be scoped conservatively to listed states.
        mentioned={s for s in STATES.values() if any(re.search(r'\b'+re.escape(s)+r'\b',t,re.I) for t in evidence)}
        if period and states and (not mentioned or mentioned.issubset(set(states))):
            scope=sorted(mentioned) if mentioned else [] if nationwide else states
            salary={'min':low,'max':high,'period':period,'currency':'USD','scopeStates':scope}
            published['scopeStates']=scope
            if nationwide and not mentioned: published['note']='Employer-published range for this U.S. remote role; actual pay may vary by location.'
    if any(r[2] is None for r in records): published['note']+=' Pay period is not specified for every range.'
    return salary,published


def normalize_posting(body, url, company, now):
    """Only explicit evidence populates filters; uncertainty is preserved."""
    host, sector = SOURCES[company]
    url = job_url(url, host)
    page = Page(body)
    candidates = []
    for script in page.scripts:
        try: candidates.extend(postings(json.loads(script)))
        except (ValueError, TypeError): continue
    if not candidates:
        adapted=extract_employer_page(company,body,url)
        if adapted:candidates.append(adapted)
    matched=[]
    for candidate in candidates:
        try:
            candidate_url=candidate.get('url') or page.canonical
            if not candidate_url and host.endswith('.myworkdayjobs.com'):
                identifier=candidate.get('identifier',{})
                identifier=str(identifier.get('value','') if isinstance(identifier,dict) else identifier)
                if identifier and re.search(r'_'+re.escape(identifier)+r'(?:-\d+)?/?$',urllib.parse.urlsplit(url).path,re.I):
                    candidate={**candidate,'url':url,'_adapter':'workday-public-jobposting'};candidate_url=url
            if posting_key(job_url(str(candidate_url or '').rstrip('/'),host))==posting_key(url): matched.append(candidate)
        except ValueError: pass
    if len(matched) != 1: raise ValueError('Missing or ambiguous matching JobPosting data; '+str(len(candidates))+' structured candidates found')
    source = matched[0]
    url=job_url((source.get('url') or page.canonical).rstrip('/'),host)
    if not isinstance(source.get('title'),str): raise ValueError('Invalid posting title')
    title = html.unescape(source['title']).strip()
    req = source.get('identifier', {})
    req = str(req.get('value', '') if isinstance(req, dict) else req).strip()
    if not title or not req: raise ValueError('Missing title or requisition')
    description = Page(html.unescape(str(source.get('description', '')))).text
    locations = [];remote_location_states=[]
    expanded_locations=[]
    for loc in as_list(source.get('jobLocation')):
        if isinstance(loc,dict):
            expanded_locations.extend({**loc,'address':address} for address in as_list(loc.get('address')) if isinstance(address,dict))
    for loc in expanded_locations:
        address = loc.get('address', {}) if isinstance(loc, dict) else {}
        if not isinstance(address,dict): continue
        country = address.get('addressCountry', '')
        if isinstance(country, dict): country = country.get('name', '')
        state = state_name(address.get('addressRegion'))
        city = address.get('addressLocality') or ''
        if not isinstance(city,str): continue
        city=city.strip()
        if not state and host.endswith('.myworkdayjobs.com'):
            explicit=re.fullmatch(r'US\s*-\s*([A-Z]{2})\s*-\s*(.+)',city)
            if explicit and state_name(explicit[1]):state=state_name(explicit[1]);city=explicit[2]
            elif str(country).upper() in ('US','USA','UNITED STATES','UNITED STATES OF AMERICA'):
                location_part=urllib.parse.urlsplit(url).path.split('/job/',1)[-1].split('/')[0]
                explicit=re.fullmatch(r'(.+)-([A-Z]{2})',location_part)
                if explicit and state_name(explicit[2]):state=state_name(explicit[2])
        if str(country).upper() in ('US', 'USA', 'UNITED STATES', 'UNITED STATES OF AMERICA') and state and city:
            item = {'city': city, 'state': state}
            if item not in locations: locations.append(item)
            if re.fullmatch(r'Remote[-, ]+(?:'+re.escape(address.get('addressRegion',''))+'|'+re.escape(state)+r'|'+next((code for code,name in STATES.items() if name==state),'')+r')',city,re.I):
                if state not in remote_location_states: remote_location_states.append(state)
    eligible = [];country_requirements=[]
    for loc in as_list(source.get('applicantLocationRequirements')):
        if not isinstance(loc, dict): continue
        if loc.get('@type')=='Country':
            country_requirements.append(str(loc.get('name','')).upper());continue
        state = state_name(loc.get('name'))
        if state and state not in eligible: eligible.append(state)
    arrangement, arrangement_evidence = 'unknown', ''
    national_remote=re.search(r'You[\u2019\']ll enjoy the flexibility to (?:work remotely|telecommute)\s*\*?\s*from anywhere within the U\.?S\.?',description,re.I)
    if not national_remote:
        national_remote=re.search(r'\b(?:remote|virtual)\s+(?:role|position|job)\s+open to candidates (?:located |residing )?anywhere (?:in|within) (?:the )?(?:United States|U\.?S\.?)\b',description,re.I)
    labeled = re.search(r'(?:Remote\s+(?:Job|Type)|Job\s+Type|Workplace\s+Type|Work\s+(?:Arrangement|Location|Type)|Location\s+Type|Role\s+Type)\s*:?\s*(Hybrid|On[- ]?site|Remote)\b', description+'\n'+page.text, re.I)
    if labeled:
        arrangement = {'hybrid':'hybrid','onsite':'on-site','remote':'remote'}[re.sub(r'[- ]','',labeled[1].lower())]
        arrangement_evidence = labeled[0]
    elif company!='fannie-mae' and str(source.get('jobLocationType','')).upper() in ('TELECOMMUTE','REMOTE','HYBRID','ON_SITE','ONSITE'):
        kind=str(source['jobLocationType']).upper()
        arrangement = 'remote' if kind in ('TELECOMMUTE','REMOTE') else 'hybrid' if kind=='HYBRID' else 'on-site'
        arrangement_evidence='JobPosting.jobLocationType='+kind
    else:
        onsite = re.search(r'This (?:position|role) is (?:expected to be 100%|a full[- ]time) on[- ]?site|This is a full[- ]time on[- ]?site role|Required Onsite \d days per week|^Onsite,\s*(?:Monday|Tuesday|Wednesday|Thursday|Friday)', description, re.I|re.M)
        if onsite: arrangement, arrangement_evidence = 'on-site', onsite[0]
        hybrid=re.search(r'\bThis (?:is a hybrid (?:position|role)|(?:position|role) is hybrid|(?:position|role) (?:follows|provides) a hybrid work (?:schedule|arrangement))\b|\bHybrid Work Model\s*:|\bHybrid:\s*This role requires associates to be in-office',description,re.I)
        if hybrid: arrangement,arrangement_evidence='hybrid',hybrid[0]
        tag=re.search(r'#LI-(Onsite|Hybrid|Remote)\b',description,re.I)
        if tag:
            arrangement={'onsite':'on-site','hybrid':'hybrid','remote':'remote'}[tag[1].lower()]
            arrangement_evidence=tag[0]
        remote = national_remote
        if remote: arrangement, arrangement_evidence = 'remote', remote[0]
    if arrangement=='unknown' and company=='general-motors':
        gm_hybrid=re.search(r'\bHybrid Work Policy\s*[-:]\s*[^\n]{0,160}\bin-office\b[^\n]{0,80}\bremote\b',description,re.I)
        if gm_hybrid: arrangement,arrangement_evidence='hybrid',gm_hybrid[0]
        categorized=re.search(r'\bThis role is categorized as (hybrid|remote|on[- ]?site)\b',description,re.I)
        if categorized:
            arrangement={'hybrid':'hybrid','remote':'remote','onsite':'on-site'}[re.sub(r'[- ]','',categorized[1].lower())];arrangement_evidence=categorized[0]
        onsite=re.search(r'\bThis is an onsite manufacturing engineering role\b|\bOn[- ]?site 5x? days per week\b',description,re.I)
        if onsite and arrangement=='unknown': arrangement,arrangement_evidence='on-site',onsite[0]
    if arrangement=='unknown' and company=='target':
        target_hybrid=re.search(r'\bThis position will operate as a Hybrid/Flex for Your Day work arrangement\b',description,re.I)
        if target_hybrid: arrangement,arrangement_evidence='hybrid',target_hybrid[0]
    if arrangement=='unknown':
        # Role declarations, rather than general company policy, technical
        # skills, recruiting assistants, or remote interviewing language.
        declaration=re.search(r'\b(?:this|the)\s+(?:(?:position|role|job)\s+(?:is|will be|offers|provides|follows)\s+|is\s+(?:an?\s+)?)(?:(?:an?|fully|100%)\s+)?(remote|hybrid|on[- ]?site|virtual)\s+(?:role|position|job|work (?:arrangement|schedule))\b|\b(?:this|the)\s+(?:position|role|job)\s+(?:is|will be)\s+(?:fully\s+|100%\s+)?(remote|hybrid|on[- ]?site|virtual)(?=[.,;\s]*$|[.,;\n])|\b(On[- ]?site) role in\b',description,re.I|re.M)
        if declaration:
            kind=next(group for group in declaration.groups() if group)
            arrangement={'remote':'remote','virtual':'remote','hybrid':'hybrid','onsite':'on-site'}[re.sub(r'[- ]','',kind.lower())]
            arrangement_evidence=declaration[0]
        elif re.search(r'\bThis is a [^.\n]{1,50}-based,\s*hybrid role\b',description,re.I):
            arrangement='hybrid';arrangement_evidence=re.search(r'\bThis is a [^.\n]{1,50}-based,\s*hybrid role\b',description,re.I)[0]
        elif re.search(r'\bThis role requires associates to be in-office [1-4] days per week[^\n]*\bvirtual work\b',description,re.I):
            arrangement='hybrid';arrangement_evidence=re.search(r'\bThis role requires associates to be in-office [1-4] days per week[^\n]*\bvirtual work\b',description,re.I)[0]
        elif national_remote:
            arrangement,arrangement_evidence='remote',national_remote[0]
        else:
            # Comcast publishes Remote as the job's structured location label.
            # It is arrangement evidence, not an eligible-state declaration.
            for loc in as_list(source.get('jobLocation')):
                address=loc.get('address',{}) if isinstance(loc,dict) else {}
                if isinstance(address,dict) and str(address.get('addressCountry','')).strip().lower()=='remote':
                    arrangement,arrangement_evidence='remote','Employer JobPosting jobLocation label: Remote'
                    break
    # An explicit employer title qualifier is arrangement evidence, but does
    # not establish nationwide or state eligibility. Description labels win.
    if arrangement=='unknown':
        qualifier=re.search(r'[\(\[]\s*(Remote|Hybrid|On[- ]?site)\s*[\)\]]|(?:^|\s[-\u2013\u2014]\s)(Remote|Hybrid|On[- ]?site)(?:\s*,[^\n]+)?\s*$',title,re.I)
        if qualifier:
            kind=next(group for group in qualifier.groups() if group)
            arrangement={'remote':'remote','hybrid':'hybrid','onsite':'on-site'}[re.sub(r'[- ]','',kind.lower())]
            arrangement_evidence='Explicit employer title qualifier: '+qualifier[0].strip()
    if arrangement=='remote' and remote_location_states:
        eligible=sorted(set(eligible+remote_location_states))
    # A posted office address is not evidence of remote eligibility.
    if arrangement != 'remote': eligible = []
    # Generic internet/home-office requirements do not impose state residency.
    residency_restricted=bool(re.search(r'\bwithin\s+\d+\s+miles\b',description,re.I))
    state_words='|'.join(re.escape(s) for s in STATES.values())
    for line in description.splitlines():
        restriction=re.search(r'\b(?:must(?: not)?|required to|need to)\s+(?:currently\s+)?(?:live|reside|be located|be based)\b|\b(?:limited to|restricted to|excluding|except|not available in|not eligible in|may not be performed in)\b',line,re.I)
        named_state=re.search(r'\b(?:'+state_words+r')\b',line,re.I) or re.search(r'\b(?:'+'|'.join(STATES)+r')\b',line)
        if restriction and named_state: residency_restricted=True
    us_allowed=any(value in ('US','USA','UNITED STATES','UNITED STATES OF AMERICA') for value in country_requirements)
    explicit_national=us_allowed and not host.endswith('.myworkdayjobs.com') or bool(national_remote and (not country_requirements or us_allowed))
    remote_scope='states' if eligible else 'nationwide' if arrangement=='remote' and explicit_national and not residency_restricted else 'unknown'
    if not locations and not eligible: return None
    travel, travel_evidence = None, ''
    no_travel = re.search(r'\b(?:Travel\s*(?:Required)?\s*:\s*(?:None|No)(?!\s+more)|No travel (?:is )?required)\b|\bTravel\s*:\s*0\s*%',page.text,re.I)
    yes_travel = re.search(r'\bTravel\s*:\s*(?:Yes\s*,?\s*)?(?:Up to\s*)?([1-9]\d?(?:\.\d+)?|100)\s*%[^\n]{0,50}',page.text,re.I)
    if not yes_travel: yes_travel=re.search(r'\b(?:Willing(?:ness)?|Ability|Required)\s+to\s+travel\s+(?:nationally\s+)?(?:up to\s+)?([1-9]\d?(?:\.\d+)?|100)\s*%[^\n]{0,50}|\b(?:up to\s+)?(?:[1-9]\d?|100)\s*%\s+(?:business\s+)?travel\b|\bthis (?:role|position) (?:may need to|requires? you to|requires? occasional) travel\b',description,re.I)
    if no_travel: travel, travel_evidence = False, no_travel[0]
    elif yes_travel: travel, travel_evidence = True, yes_travel[0]
    employment = 'Not specified'
    raw_type = ' '.join(str(x) for x in as_list(source.get('employmentType'))).lower().replace('_','-')
    for pattern, value in [('full-time','Full-time'),('full time','Full-time'),('part-time','Part-time'),('part time','Part-time'),('contract','Contract'),('temporary','Temporary'),('intern','Internship')]:
        if pattern in raw_type: employment = value; break
    if employment == 'Not specified':
        labeled_type = re.search(r'Time\s+Type\s*:\s*(Full[- ]time|Part[- ]time)', page.text, re.I)
        if labeled_type: employment = 'Full-time' if labeled_type[1].lower().startswith('full') else 'Part-time'
        explicit_type=re.search(r'\bThis\s+(?:position|role|job)\s+is\s+(?:a\s+)?(full[- ]time|part[- ]time)\b',description,re.I)
        if explicit_type: employment='Full-time' if explicit_type[1].lower().startswith('full') else 'Part-time'
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
    text_salary, published_pay = extract_published_pay(description,locations,company,nationwide=remote_scope=='nationwide')
    if salary is None and text_salary:
        salary=text_salary
        salary_evidence='Explicit employer pay text with stated period; scoped to listed or explicitly named states'
    today = now.astimezone(ZoneInfo('America/New_York')).date().isoformat()
    deadline = date_only(source.get('validThrough'))
    if not deadline and company=='target' and source.get('validThrough'):
        try: deadline=datetime.strptime(str(source['validThrough']),'%m/%d/%Y').date().isoformat()
        except ValueError: pass
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
        'remoteScope':remote_scope, 'eligibleStates':eligible,
        'locationNote':('Remote within the U.S. · Employer-listed locations: ' if remote_scope=='nationwide' else 'Remote · Eligible states not verified · Employer-listed locations: ' if arrangement=='remote' and remote_scope=='unknown' else '')+('; '.join(l['city']+', '+l['state'] for l in locations) or 'Employer specifies eligible states: '+', '.join(eligible)),
        'employmentType':employment, 'salary':salary,
        'publishedPay':published_pay,
        'salaryNote':published_pay['note'] if published_pay else 'Structured employer pay for the listed state.' if salary else 'Pay or geographic scope not verified automatically. See employer posting.',
        'travelRequired':travel, 'travelNote':travel_evidence or 'Travel not verified automatically.',
        'postedAt':posted, 'closesAt':deadline,
        'reviewedAt':today, 'status':'closed' if source.get('_employerClosed') or deadline and deadline<today else 'reviewed', 'sector':sector,
        'sourceNote':'Automatically checked against the official individual posting. Missing fields remain unknown; pilot coverage is limited.'+(' '+deadline_note if deadline_note else ''),
        'checkedAt':now.isoformat(), 'collectionMethod':source.get('_adapter') or 'official-jobposting-jsonld',
        'sourceHash':hashlib.sha256(json.dumps({'structured':source,'arrangement':arrangement_evidence,'remoteScope':remote_scope,'travel':travel_evidence,'employmentType':employment,'deadline':deadline,'publishedPay':published_pay},sort_keys=True,ensure_ascii=False).encode()).hexdigest(),
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
        for attempt in range(3):
            try:
                with self.opener.open(req, timeout=30) as response:
                    limit=32_000_000 if urllib.parse.urlsplit(url).path.endswith('.xml') else 25_000_000
                    raw = response.read(limit+1)
                    if len(raw)>limit: raise SourceError('Response exceeds size limit')
                    return response.status, raw.decode('utf-8-sig')
            except urllib.error.HTTPError as error:
                if error.code in (404,410): return error.code, ''
                # Never retry access denial or rate limiting.
                raise SourceError('Employer request failed: HTTP '+str(error.code)) from error
            except (http.client.IncompleteRead,http.client.RemoteDisconnected,TimeoutError,ConnectionResetError,urllib.error.URLError) as error:
                if attempt==2: raise SourceError('Interrupted employer download after three attempts: '+str(error)) from error
                time.sleep(2*(attempt+1))


def discover(client):
    ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    # Sitemaps are published discovery documents, not excluded search endpoints.
    published=client.robots.site_maps() if client.robots else None
    queue=[u for u in (published or ['https://'+client.host+'/sitemap.xml']) if urllib.parse.urlsplit(u).hostname==client.host]
    seen=set();found={};dates={}
    while queue and len(seen)<20:
        sitemap=queue.pop(0)
        if sitemap in seen: continue
        seen.add(sitemap)
        status,body=client.get(sitemap)
        if status!=200: continue
        try: root=ET.fromstring(body)
        except ET.ParseError as error: raise SourceError('Invalid employer sitemap response') from error
        if root.tag==ns+'sitemapindex':
            children=[entry.findtext(ns+'loc') for entry in root.findall(ns+'sitemap')]
            children=[u for u in children if u and urllib.parse.urlsplit(u).hostname==client.host]
            children.sort(key=lambda u:('job' not in u.lower(),-language_priority(u),u))
            queue.extend(children)
        elif root.tag==ns+'urlset':
            for entry in root.findall(ns+'url'):
                url=entry.findtext(ns+'loc') or ''
                try:url=job_url(url,client.host)
                except ValueError:continue
                key=posting_key(url)
                if key not in found or language_priority(url)>language_priority(found[key]): found[key]=url
                modified=entry.findtext(ns+'lastmod') or ''
                dates[key]=max(dates.get(key,''),modified)
        else: raise SourceError('Unexpected sitemap format; manual adapter review required')
    if not found and client.host in ('jobs.cardinalhealth.com','careers.bankofamerica.com'):
        landing='https://'+client.host+'/'
        status,body=client.get(landing)
        if status==200:
            for node in Document(body).nodes:
                if node['tag']!='a':continue
                try:url=job_url(urllib.parse.urljoin(landing,node['attrs'].get('href','')),client.host)
                except ValueError:continue
                found[posting_key(url)]=url
    if not found: raise SourceError('Reviewed discovery contains no individual job URLs')
    client.discovery_dates=dates
    client.discovery_limited=bool(queue)
    return found


def reconcile(company, old_jobs, state, discovered, fetch, now, max_new=20, cap=100, discovery_dates=None):
    """Never close by absence from a sitemap or partial crawl."""
    host = SOURCES[company][0]
    previous = [j for j in old_jobs if j['companyId']==company]
    by_id = {j['id']:copy.deepcopy(j) for j in previous if recent_posting(j,now)}
    old_urls = {posting_key(j['url']):j for j in previous}
    source_state = copy.deepcopy(state)
    rejected = source_state.setdefault('rejected', {})
    quarantined = {k:v for k,v in source_state.setdefault('quarantined',{}).items() if (now-datetime.fromisoformat(v)).total_seconds()<86400}
    source_state['quarantined']=quarantined
    missing = source_state.setdefault('missing', {})
    report = {'discovered':len(discovered),'checked':0,'added':0,'changed':0,'closed':0,'skipped':0,'outsidePostingWindow':len(previous)-len(by_id),'warnings':[],'errors':[]}
    active = [j for j in previous if j['status']!='closed' and recent_posting(j,now)]
    # Existing records are checked even when sitemap discovery stops mentioning them.
    queue = [(discovered.get(k,j['url']),j) for k,j in old_urls.items() if j['status']!='closed' and recent_posting(j,now)]
    room = max(0, cap-len(active))
    candidates = [(k,u) for k,u in discovered.items() if k not in old_urls and k not in rejected and k not in quarantined]
    candidates.sort(key=lambda pair:((discovery_dates or {}).get(pair[0],''),discovery_priority(pair[0])), reverse=True)
    # A small discovery allowance prevents the newest general roles from
    # crowding out remote-labeled routes. URLs only prioritize inspection;
    # fetched employer evidence still determines arrangement and posting age.
    hint_count=min(5,max_new//4)
    hinted=[pair for pair in candidates if re.search(r'(?:/|[-_])remote(?:/|[-_]|$)',urllib.parse.urlsplit(pair[1]).path,re.I)][:hint_count]
    hinted_keys={pair[0] for pair in hinted}
    candidates=hinted+[pair for pair in candidates if pair[0] not in hinted_keys]
    reopen = [(discovered[k],j) for k,j in old_urls.items() if j['status']=='closed' and k in discovered and recent_posting(j,now)]
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
                rejected[posting_key(url)] = now.isoformat(); report['skipped'] += 1
                continue
            # Requisition identity is stable across title/slug changes.
            if old and old['requisitionId'] != job['requisitionId']: raise ValueError('Requisition identity changed')
            if not recent_posting(job,now):
                by_id.pop(job['id'],None)
                rejected[posting_key(url)]=now.isoformat()
                report['outsidePostingWindow']+=1
                continue
            missing.pop(job['id'],None)
            existing = by_id.get(job['id'])
            if existing:
                if existing.get('sourceHash') != job['sourceHash']: report['changed'] += 1
            else: report['added'] += 1
            by_id[job['id']] = job
            if job['status']=='closed' and (not existing or existing['status']!='closed'): report['closed'] += 1
        except (ValueError,SourceError,urllib.error.URLError,TimeoutError) as error:
            if old is not None and isinstance(error,ValueError) and re.search(r'\b(?:Sorry[,!]?\s+(?:this|the)\s+(?:job|position)\s+is\s+no longer available|This\s+(?:job|position)\s+(?:has expired|has been filled|is no longer available))\b',Page(body).text,re.I):
                first=missing.get(old['id'])
                if first and (now-datetime.fromisoformat(first)).total_seconds()>=21600: closures.append(old['id'])
                elif not first: missing[old['id']]=now.isoformat()
                continue
            if old is None and isinstance(error,ValueError):
                report['warnings'].append({'url':url,'error':'Candidate quarantined: '+str(error)[:180]})
                source_state.setdefault('quarantined',{})[posting_key(url)]=now.isoformat()
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
    report['pendingClosureChecks']=len(source_state['missing'])
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
    report = {'schemaVersion':1,'attemptedAt':now.isoformat(),'postingWindowDays':POSTING_MAX_AGE_DAYS,'coverage':'U.S. postings published within the past 14 days. Bounded pilot: at most 100 tracked active postings per employer; up to 20 new candidates per employer per scheduled/manual run. Not a complete feed.','sources':{}}
    jobs = data['jobs']
    successes = 0
    def collect(company):
        host,sector=SOURCES[company]
        try:
            client = Client(host)
            discovered = discover(client)
            refreshed, source_state, result = reconcile(company,data['jobs'],state.get(company,{}),discovered,client.get,now,max_new=max_new,discovery_dates=client.discovery_dates)
            result['discoveryLimited']=client.discovery_limited
            if not result['errors']:
                result['lastSuccessfulAt']=now.isoformat()
            else:
                result['lastSuccessfulAt']=data.get('automation',{}).get('sources',{}).get(company,{}).get('lastSuccessfulAt')
            return company,refreshed,source_state,result
        except Exception as error:
            result={'errors':[{'error':str(error)[:300]}],'lastSuccessfulAt':data.get('automation',{}).get('sources',{}).get(company,{}).get('lastSuccessfulAt')}
            return company,None,None,result
    with ThreadPoolExecutor(max_workers=3) as pool:
        for future in as_completed([pool.submit(collect,key) for key in SOURCES]):
            company,refreshed,source_state,result=future.result()
            if refreshed is not None:
                jobs=[j for j in jobs if j['companyId']!=company]+refreshed
                state[company]=source_state
            if not result['errors']: successes+=1
            report['sources'][company]=result
            print(company+': '+str(result.get('activeTracked','retained'))+' tracked; '+str(len(result['errors']))+' errors',flush=True)
    data['jobs']=sorted(jobs,key=lambda j:j['id'])
    data['automation']=report
    data['method']='Official employer sitemap discovery and individual JobPosting checks; bounded employer pilot.'
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
