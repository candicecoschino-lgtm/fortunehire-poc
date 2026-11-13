"""Reviewed first-party page formats. Missing evidence is never synthesized."""
import json
import re
from datetime import datetime
from html.parser import HTMLParser

VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
class Document(HTMLParser):
    def __init__(self,body):
        super().__init__(convert_charrefs=True)
        self.root={'tag':'root','attrs':{},'children':[]};self.stack=[self.root];self.nodes=[]
        self.feed(body)
    def handle_starttag(self,tag,attrs):
        node={'tag':tag,'attrs':dict(attrs),'children':[]};self.nodes.append(node);self.stack[-1]['children'].append(node)
        if tag not in VOID:self.stack.append(node)
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if tag not in VOID:self.handle_endtag(tag)
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i]['tag']==tag:del self.stack[i:];break
    def handle_data(self,value):self.stack[-1]['children'].append(value)
    def find(self,tag=None,**attrs):
        return next((n for n in self.nodes if (tag is None or n['tag']==tag) and all(n['attrs'].get(k)==v for k,v in attrs.items())),None)

def text(node):
    if not node:return ''
    if isinstance(node,str):return node
    if node['tag'] in ('script','style'):return ''
    separator='\n' if node['tag'] in ('p','div','section','li','h1','h2','h3','dt','dd','br') else ' '
    return separator+''.join(text(child) for child in node['children'])+separator

def walmart(document,url):
    node=document.find('script',id='__NEXT_DATA__')
    if not node:return None
    payload=json.loads(''.join(x for x in node['children'] if isinstance(x,str)))
    source=payload.get('props',{}).get('pageProps',{}).get('jobDetails',{})
    req=source.get('jobId');status=source.get('requisitionStatus',{}).get('id')
    if not req or req.lower() not in url.lower().split('/'):return None
    page_req=payload.get('props',{}).get('pageProps',{}).get('jobId')
    if page_req and page_req!=req:raise ValueError('Conflicting Walmart posting identity')
    if status not in ('OPEN','CLOSED','FILLED','CANCELLED'):raise ValueError('Unverified Walmart requisition status')
    locations=[]
    for loc in [source.get('primaryLocation')]+(source.get('additionalLocations') or []):
        if not isinstance(loc,dict):continue
        locations.append({'address':{'addressCountry':loc.get('countryCode') or loc.get('country'),'addressRegion':loc.get('stateCode') or loc.get('state'),'addressLocality':loc.get('city')}})
    job={'@type':'JobPosting','identifier':req,'url':url,'title':source.get('jobPostingTitle') or source.get('title'),'datePosted':source.get('jobPostingStartDate'),'description':source.get('jobPostingDescription') or source.get('description',''),'employmentType':[x.get('value','') for x in (source.get('employmentTypes') or []) if isinstance(x,dict)],'jobLocation':locations,'_employerClosed':status!='OPEN','_adapter':'walmart-next-data'}
    # OPEN is the explicit requisition status. The page also contains an
    # unrelated `active` flag; do not reinterpret that flag as a closure.
    ranges=source.get('payRange') or []
    currency=source.get('payPlanData',{}).get('currencyReference',{}).get('currencyId')
    period={'Hourly':'HOUR','Annual':'YEAR','Annually':'YEAR'}.get(source.get('payFrequency'))
    if len(ranges)==1 and isinstance(ranges[0],dict) and currency=='USD' and period:
        try: low,high=float(ranges[0]['min']),float(ranges[0]['max'])
        except (KeyError,TypeError,ValueError):pass
        else:job['baseSalary']={'currency':'USD','value':{'unitText':period,'minValue':low,'maxValue':high}}
    return job

def disney(document,url):
    header=document.find(id='job-details-1');description=document.find(id='job-details-3')
    if not header or not description:return None
    attrs=header['attrs'];req=attrs.get('data-tm-job-id');title=attrs.get('data-tm-job-name')
    if not req or not title:return None
    if attrs.get('data-job-id')!=url.rstrip('/').rsplit('/',1)[-1]:return None
    posted=None
    try:posted=datetime.strptime(attrs.get('data-tm-job-date-posted',''),'%m/%d/%Y').date().isoformat()
    except ValueError:pass
    locations=[]
    for label in attrs.get('data-tm-job-location','').split(' / '):
        parts=[p.strip() for p in label.split(',')]
        if len(parts)==3:locations.append({'address':{'addressLocality':parts[0],'addressRegion':parts[1],'addressCountry':parts[2]}})
    return {'@type':'JobPosting','identifier':req,'title':title,'url':url,'datePosted':posted,'description':text(description),'jobLocation':locations,'_adapter':'disney-page-metadata'}

def phillips(document,url):
    def prop(name):
        node=document.find(itemprop=name)
        return node['attrs'].get('content') or text(node).strip() if node else None
    def date(value):
        try:return datetime.strptime(value or '','%a %b %d %H:%M:%S UTC %Y').date().isoformat()
        except ValueError:return None
    title=prop('title');description=prop('description');posted=date(prop('datePosted'))
    posting_id=url.rstrip('/').rsplit('/',1)[-1]
    if not title or not description or not posted or not posting_id.isdigit():return None
    deadlines=[d for d in [date(prop('validThrough'))] if d]
    for match in re.finditer(r'requisition closing date of\s+(\d{1,2}/\d{1,2}/\d{4})',description,re.I):
        try:deadlines.append(datetime.strptime(match[1],'%m/%d/%Y').date().isoformat())
        except ValueError:pass
    return {'@type':'JobPosting','identifier':posting_id,'_identifierType':'posting-id','url':url,'title':title,'description':description,'datePosted':posted,'validThrough':min(deadlines) if deadlines else None,'jobLocation':{'address':{'addressCountry':prop('addressCountry'),'addressRegion':prop('addressRegion'),'addressLocality':prop('addressLocality')}},'_adapter':'phillips66-public-microdata'}

def extract(company,body,url):
    if company not in ('walmart','disney','phillips-66'):return None
    document=Document(body)
    if company=='walmart':return walmart(document,url)
    return disney(document,url) if company=='disney' else phillips(document,url)
