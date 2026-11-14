"""Reviewed first-party page formats. Missing evidence is never synthesized."""
import json
import re
import ast
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urlsplit, urljoin, parse_qs, unquote
from zoneinfo import ZoneInfo

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

def verizon(document,url):
    # Read JSON arguments in the server-rendered stream without executing JS.
    parts=[]
    for node in document.nodes:
        if node['tag']!='script':continue
        script=''.join(x for x in node['children'] if isinstance(x,str))
        prefix='self.__next_f.push('
        if not script.startswith(prefix):continue
        try:value=json.JSONDecoder().raw_decode(script[len(prefix):])[0]
        except (ValueError,TypeError):continue
        if isinstance(value,list) and len(value)==2 and value[0]==1 and isinstance(value[1],str):parts.append(value[1])
    matches=[];req=urlsplit(url).path.strip('/').split('/')[1]
    def walk(value,depth=0):
        if depth>40:return
        if isinstance(value,dict):
            if str(value.get('Id','')).lower()==req.lower() and 'DisplayDate' in value:matches.append(value)
            for child in value.values():walk(child,depth+1)
        elif isinstance(value,list):
            for child in value:walk(child,depth+1)
        elif isinstance(value,str) and value.startswith(('{','[')):
            try:walk(json.loads(value),depth+1)
            except ValueError:pass
    for line in ''.join(parts).splitlines():
        try:walk(json.loads(line.partition(':')[2]))
        except ValueError:pass
    unique={json.dumps(value,sort_keys=True):value for value in matches}
    if len(unique)!=1:return None
    source=next(iter(unique.values()))
    if not any(urlsplit(urljoin(url,row.get('Url',''))).path.rstrip('/')==urlsplit(url).path.rstrip('/') for row in source.get('Urls',[])):return None
    page=document.find(**{'data-testid':'job-page','data-job-id':source['Id']})
    if not page:return None
    def descendants(node):
        if isinstance(node,dict):
            yield node
            for child in node['children']:yield from descendants(child)
    descriptions=[node for node in descendants(page) if node['attrs'].get('class')=='wysiwyg']
    if len(descriptions)!=1:return None
    return {'@type':'JobPosting','url':url,'identifier':source.get('Reference'),'title':source.get('Title'),'description':text(descriptions[0]),'datePosted':source.get('DisplayDate'),'validThrough':source.get('DueDate'),'jobLocation':[{'address':{'addressLocality':loc.get('City'),'addressRegion':loc.get('Region'),'addressCountry':loc.get('Country')}} for loc in source.get('Locations',[])],'_adapter':'verizon-public-page-data'}

def oracle(body,url):
    try:items=json.loads(body).get('items',[])
    except (ValueError,AttributeError):return None
    req=urlsplit(url).path.rstrip('/').rsplit('/',1)[-1]
    if len(items)!=1 or str(items[0].get('Id',''))!=req:return None
    source=items[0]
    if not source.get('ExternalPostedStartDate') or not source.get('ExternalDescriptionStr'):return None
    locations=[]
    for loc in (source.get('workLocation') or [])+(source.get('otherWorkLocations') or []):
        locations.append({'address':{'addressLocality':loc.get('TownOrCity'),'addressRegion':loc.get('Region2'),'addressCountry':loc.get('Country')}})
    description='\n'.join(str(source.get(key) or '') for key in ('ExternalDescriptionStr','ExternalQualificationsStr','ExternalResponsibilitiesStr'))
    schedule={'Full time':'FULL_TIME','Part time':'PART_TIME'}.get(source.get('JobSchedule'))
    arrangement={'ORA_ON_SITE':'ON_SITE','ORA_HYBRID':'HYBRID','ORA_REMOTE':'REMOTE'}.get(source.get('WorkplaceTypeCode'))
    # Plain public labels also occur when the corresponding code is absent.
    arrangement=arrangement or {'On-site':'ON_SITE','Hybrid':'HYBRID','Remote':'REMOTE'}.get(source.get('WorkplaceType'))
    posted=source['ExternalPostedStartDate']
    if 'T' in posted:
        try:
            timestamp=datetime.fromisoformat(posted.replace('Z','+00:00'))
            if timestamp.tzinfo is None:return None
            posted=timestamp.astimezone(ZoneInfo('America/New_York')).date().isoformat()
        except ValueError:return None
    return {'@type':'JobPosting','identifier':req,'title':source.get('Title'),'url':url,'datePosted':posted,'validThrough':source.get('ExternalPostedEndDate'),'description':description,'employmentType':schedule,'jobLocationType':arrangement,'jobLocation':locations,'_adapter':'oracle-public-requisition-details'}

def valero(document,body,url):
    history=document.find('input',id='initialHistory')
    mapping=re.search(r'descRequisition:\s*\{\s*_size:\s*1,.*?_hlid:\s*(\[[^\]]+\])',body,re.S)
    if not history or not mapping:return None
    try:fields=ast.literal_eval(mapping[1])
    except (ValueError,SyntaxError):return None
    if not isinstance(fields,list) or not all(isinstance(field,str) and re.fullmatch(r'reqlistitem\.[a-z]+',field) for field in fields):return None
    parts=history['attrs'].get('value','').split('!|!')
    if len(parts)<3+len(fields) or parts[2]!='descRequisition':return None
    data={}
    for field,value in zip(fields,parts[3:3+len(fields)]):
        if field not in {'reqlistitem.contestnumber','reqlistitem.title','reqlistitem.description','reqlistitem.qualification','reqlistitem.primarylocation','reqlistitem.postingdate','reqlistitem.unpostingdate'}:continue
        value=unquote(value).removeprefix('!*!').replace('\\:',':')
        if field in data and data[field]!=value:raise ValueError('Conflicting Taleo display values')
        data[field]=value
    req=data.get('reqlistitem.contestnumber')
    if parse_qs(urlsplit(url).query).get('job')!=[req]:return None
    def date(value):
        try:return datetime.strptime(value or '','%b %d, %Y, %I:%M:%S %p').date().isoformat()
        except ValueError:return None
    posted=date(data.get('reqlistitem.postingdate'))
    location=(data.get('reqlistitem.primarylocation') or '').split('-',2)
    if not posted or len(location)!=3 or location[0]!='US':return None
    return {'@type':'JobPosting','identifier':req,'url':url,'title':data.get('reqlistitem.title'),'description':data.get('reqlistitem.description','')+'\n'+data.get('reqlistitem.qualification',''),'datePosted':posted,'validThrough':date(data.get('reqlistitem.unpostingdate')),'jobLocation':{'address':{'addressCountry':'US','addressRegion':location[1],'addressLocality':location[2]}},'_adapter':'valero-public-taleo-display-data'}

def amazon(body,url):
    try:data=json.loads(body);source=data['amazonPosting']
    except (ValueError,KeyError,TypeError):return None
    req=urlsplit(url).path.strip('/').split('/')[2]
    if str(source.get('id_icims',''))!=req or data.get('pageTitle')!=source.get('title'):return None
    try:posted=datetime.strptime(source.get('posted_date',''),'%B %d, %Y').date().isoformat()
    except ValueError:return None
    locations=[]
    for raw in source.get('locations',[]):
        try:loc=json.loads(raw) if isinstance(raw,str) else raw
        except ValueError:continue
        if isinstance(loc,dict):locations.append({'address':{'addressCountry':loc.get('countryIso2a') or loc.get('normalizedCountryCode'),'addressRegion':loc.get('normalizedStateName') or loc.get('region'),'addressLocality':loc.get('city') or loc.get('normalizedCityName')}})
    if not locations and source.get('country_code') in ('US','USA'):
        locations.append({'address':{'addressCountry':source['country_code'],'addressRegion':source.get('state'),'addressLocality':source.get('city')}})
    return {'@type':'JobPosting','identifier':req,'_identifierType':'posting-id','url':data.get('pageUrl'),'title':source.get('title'),'datePosted':posted,'description':data.get('pageDescription',''),'jobLocation':locations,'employmentType':{'full-time':'FULL_TIME','part-time':'PART_TIME'}.get(source.get('job_schedule_type')),'_adapter':'amazon-public-search-and-role-page'}

def ups_opening_pay(body,posting_id):
    marker=re.search(r'phApp\.ddo\s*=\s*',body)
    if not marker:return None
    try:job=json.JSONDecoder().raw_decode(body[marker.end():])[0].get('jobDetail',{}).get('data',{}).get('job',{})
    except (ValueError,AttributeError):return None
    if str(job.get('jobId','')).lower()!=posting_id.lower() or job.get('country') not in ('United States','United States of America','US','USA'):return None
    raw=job.get('openingPayRate','')
    if not isinstance(raw,str):return None
    match=re.fullmatch(r'\$\s*(\d+(?:\.\d{1,2})?)\s*/\s*(?:hour|hr)',raw,re.I)
    if not match or float(match[1])<=0:return None
    return float(match[1]),raw

def extract(company,body,url):
    if company=='apple':
        from apple_public import extract as apple
        return apple(body,url)
    if company=='amazon':return amazon(body,url)
    if company in ('dell','kroger'):return oracle(body,url)
    if company not in ('walmart','disney','phillips-66','verizon','valero'):return None
    document=Document(body)
    if company=='valero':return valero(document,body,url)
    if company=='verizon':return verizon(document,url)
    if company=='walmart':return walmart(document,url)
    return disney(document,url) if company=='disney' else phillips(document,url)
