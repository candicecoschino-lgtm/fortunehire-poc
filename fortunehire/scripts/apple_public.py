"""Read only the public Apple page's literal serialized job data."""
import json,re
from urllib.parse import urlsplit
from employer_adapters import Document,text

ROLE=re.compile(r'/en-us/details/(\d+(?:-\d+)?)/[^/]+/?$')

def role_id(url):
    p=urlsplit(url)
    if p.scheme!='https' or p.netloc!='jobs.apple.com':return None
    m=ROLE.fullmatch(p.path)
    return m[1] if m else None

def extract(body,url):
    req=role_id(url)
    if not req:return None
    matches=[]
    def walk(v,depth=0):
        if depth>30:return
        if isinstance(v,dict):
            if 'jobNumber' in v:
                if v['jobNumber']==req:matches.append(v)
                return
            for x in v.values():walk(x,depth+1)
        elif isinstance(v,list):
            for x in v:walk(x,depth+1)
    for n in Document(body).nodes:
        if n['tag']!='script':continue
        s=''.join(x for x in n['children'] if isinstance(x,str))
        prefix='window.__staticRouterHydrationData = JSON.parse('
        if s.startswith(prefix):
            encoded=json.JSONDecoder().raw_decode(s[len(prefix):])[0]
            walk(json.loads(encoded))
    if len(matches)!=1:return None
    source=matches[0];loc=source.get('selectedLocation',{})
    # A country-wide retail pipeline is not a verified state-specific opening.
    if loc.get('active') is not True or loc.get('countryID')!='iso-country-USA' or not loc.get('city') or not loc.get('stateProvince'):return None
    if '-' not in req or req.rsplit('-',1)[1]!=loc.get('postingIdentifier'):return None
    dates=source.get('postingPostLocationData',{}).get('en_US',{})
    date=dates.get(loc.get('id'),{}).get('postingDate')
    if not isinstance(date,str) or not re.match(r'^\d{4}-\d{2}-\d{2}T',date):return None
    description='\n'.join(source.get(k,'') or '' for k in ('jobSummary','description','responsibilities','minimumQualifications','preferredQualifications'))
    for footer in source.get('postingFooters',[]):
        if footer.get('postLocationId')!=loc.get('id'):continue
        for item in footer.get('localizations',{}).get('en_US',[]):
            if item.get('name') in ('Pay & Benefits','Application Deadline'):
                description+='\n'+text(Document(item.get('content','')).root)
    return {'@type':'JobPosting','identifier':req,'_identifierType':'posting-id','title':source.get('postingTitle'),'url':url,'datePosted':date,'description':description,'jobLocation':{'address':{'addressCountry':'US','addressRegion':loc['stateProvince'],'addressLocality':loc['city']}},'_adapter':'apple-public-location-posting'}
