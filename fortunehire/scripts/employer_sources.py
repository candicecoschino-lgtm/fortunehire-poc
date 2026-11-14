"""Bounded public search interfaces explicitly linked by the employer portals."""
import json
import html
from urllib.parse import urlencode, urlsplit, parse_qs
import re
from employer_adapters import Document, text
from datetime import datetime

def amazon_rows(body):
    data=json.loads(body)
    if data.get('error') or not isinstance(data.get('jobs'),list):raise ValueError('Invalid Amazon public search result')
    return data

def amazon_id(path):
    match=re.fullmatch(r'/en/jobs/(\d+)/[^/?]+/?',path)
    return match[1] if match else None

ORACLE = {
    'enterpriseplatform.dell.com': ('enterpriseplatform.dell.com','CX_1001','/hcmUI/CandidateExperience/en/sites/CX_1001'),
    'www.krogerfamilycareers.com': ('eluq.fa.us2.oraclecloud.com','CX_2001','/en/sites/CX_2001'),
}
API='/hcmRestApi/resources/11.13.18.05/'

def public_search(client, client_factory):
    """Inspect at most 60 recent results; publishing still checks each job."""
    if client.host=='www.jobs-ups.com':
        status,body=client.get('https://www.jobs-ups.com/us/en/search-results')
        marker=re.search(r'phApp\.ddo\s*=\s*',body)
        if status!=200 or not marker:raise ValueError('Missing UPS public search data')
        data=json.JSONDecoder().raw_decode(body[marker.end():])[0].get('eagerLoadRefineSearch',{})
        rows=data.get('data',{}).get('jobs')
        if not isinstance(rows,list):raise ValueError('Invalid UPS public search data')
        found={};dates={}
        for row in rows[:20]:
            req=str(row.get('jobId',''));title=row.get('title','')
            if row.get('country') not in ('US','USA','United States','United States of America') or not re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}',req) or not isinstance(title,str):continue
            slug=re.sub(r'[^A-Za-z0-9]+','-',title).strip('-')
            if not slug:continue
            found[req]='https://'+client.host+'/us/en/job/'+req+'/'+slug;dates[req]=row.get('postedDate') or ''
        client.discovery_dates=dates;client.discovery_limited=data.get('totalHits',0)>len(found);client.discovery_warnings=[]
        return found
    if client.host=='www.amazon.jobs':
        status,body=client.get('https://www.amazon.jobs/en/search.json?'+urlencode({'sort':'recent','result_limit':20,'country[]':'USA'}))
        if status!=200:raise ValueError('Amazon public search unavailable')
        data=amazon_rows(body);found={};dates={};records={}
        for row in data['jobs'][:20]:
            req=str(row.get('id_icims',''));path=row.get('job_path','')
            if row.get('country_code') not in ('US','USA') or amazon_id(path)!=req:continue
            found[req]='https://'+client.host+path;records[req]=row
            try:dates[req]=datetime.strptime(row.get('posted_date',''),'%B %d, %Y').date().isoformat()
            except ValueError:dates[req]=''
        client.amazon_records=records;client.discovery_dates=dates;client.discovery_limited=data.get('hits',0)>len(found);client.discovery_warnings=[]
        return found
    if client.host=='careers.costco.com':
        status,body=client.get('https://careers.costco.com/api/jobs?'+urlencode({'sortBy':'posted_date','descending':'true','limit':20,'page':1}))
        if status!=200:raise ValueError('Costco public search unavailable')
        data=json.loads(body)
        if not isinstance(data.get('jobs'),list):raise ValueError('Invalid Costco public search result')
        found={};dates={}
        for wrapper in data['jobs'][:20]:
            row=wrapper.get('data',{});req=str(row.get('req_id',''));slug=str(row.get('slug',''))
            if not req.isdigit() or req!=slug or row.get('country') not in ('United States','USA','US'):continue
            found[req]='https://'+client.host+'/jobs/'+req;dates[req]=row.get('posted_date') or ''
        client.discovery_dates=dates;client.discovery_limited=data.get('totalCount',0)>len(found);client.discovery_warnings=[]
        return found
    if client.host=='valero.taleo.net':
        landing=client_factory('www.valero.com')
        status,body=landing.get('https://www.valero.com/careers')
        if status!=200:raise ValueError('Valero public career links unavailable')
        found={}
        for node in Document(body).nodes:
            if node['tag']!='a':continue
            parsed=urlsplit(node['attrs'].get('href',''))
            if parsed.scheme!='https' or parsed.netloc!=client.host or parsed.path!='/careersection/2/jobdetail.ftl':continue
            values=parse_qs(parsed.query).get('job',[])
            if len(values)==1 and re.fullmatch(r'[A-Za-z0-9]{5,12}',values[0]):found[values[0].upper()]='https://'+client.host+parsed.path+'?'+urlencode({'job':values[0]})
        client.discovery_dates={};client.discovery_limited=True;client.discovery_warnings=[]
        return found
    config=ORACLE.get(client.host)
    if not config:return None
    datahost,site,jobbase=config
    data_client=client if datahost==client.host else client_factory(datahost)
    client.oracle_data_client=data_client
    found={};dates={};limited=False
    for offset in (0,20,40):
        params={'onlyData':'true','expand':'requisitionList','finder':f'findReqs;siteNumber={site},limit=20,offset={offset},sortBy=POSTING_DATES_DESC'}
        status,body=data_client.get('https://'+datahost+API+'recruitingCEJobRequisitions?'+urlencode(params))
        if status!=200:raise ValueError('Public Oracle search is unavailable')
        items=json.loads(body).get('items',[])
        if len(items)!=1 or items[0].get('SiteNumber')!=site:raise ValueError('Unexpected Oracle career site')
        result=items[0];rows=result.get('requisitionList')
        if not isinstance(rows,list):raise ValueError('Missing Oracle public requisition list')
        for row in rows:
            req=str(row.get('Id',''))
            if row.get('PrimaryLocationCountry')!='US' or not req or not req.replace('-','').isalnum():continue
            found[req]='https://'+client.host+jobbase+'/job/'+req
            dates[req]=row.get('PostedDate') or ''
        limited=offset+len(rows)<result.get('TotalJobsCount',0)
        if len(found)>=20 or len(rows)<20:break
    client.discovery_dates=dates;client.discovery_limited=limited;client.discovery_warnings=[]
    return found

def public_fetch(client, url, client_factory):
    """Check the public job URL, then read its employer-published details."""
    status,body=client.get(url)
    if client.host=='www.amazon.jobs' and status==200:
        req=amazon_id(urlsplit(url).path)
        if not req:raise ValueError('Invalid Amazon individual posting route')
        record=getattr(client,'amazon_records',{}).get(req)
        if record is None:
            search_status,search_body=client.get('https://'+client.host+'/en/search.json?'+urlencode({'base_query':req}))
            if search_status!=200:raise ValueError('Amazon posting lookup unavailable')
            matches=[row for row in amazon_rows(search_body)['jobs'] if str(row.get('id_icims',''))==req and amazon_id(row.get('job_path',''))==req]
            if len(matches)!=1:raise ValueError('Missing or ambiguous Amazon posting lookup')
            record=matches[0]
        record={**record,'title':html.unescape(str(record.get('title',''))).strip()}
        doc=Document(body);title=doc.find('h1',**{'class':'title'});identity=doc.find('meta',property='og:url');scope=doc.find(id='job-detail-body')
        def descendants(node):
            if isinstance(node,dict):
                yield node
                for child in node['children']:yield from descendants(child)
        contents=[node for node in descendants(scope) if node['attrs'].get('class')=='content']
        if not title or not identity or amazon_id(urlsplit(identity['attrs'].get('content','')).path)!=req or text(title).strip()!=record.get('title') or len(contents)!=1:
            raise ValueError('Conflicting Amazon page and public search identity')
        return 200,json.dumps({'amazonPosting':record,'pageDescription':text(contents[0]),'pageTitle':text(title).strip(),'pageUrl':identity['attrs']['content']})
    config=ORACLE.get(client.host)
    if not config or status!=200:return status,body
    datahost,site,jobbase=config
    path=urlsplit(url).path
    if not path.startswith(jobbase+'/job/'):raise ValueError('Unexpected Oracle individual-job route')
    req=path[len(jobbase+'/job/'):]
    if not req or not req.replace('-','').isalnum():raise ValueError('Invalid Oracle posting identifier')
    data_client=getattr(client,'oracle_data_client',None)
    if data_client is None:
        data_client=client if datahost==client.host else client_factory(datahost)
        client.oracle_data_client=data_client
    params={'onlyData':'true','expand':'workLocation,otherWorkLocations,secondaryLocations','finder':f'ById;siteNumber={site},Id={req}'}
    status,body=data_client.get('https://'+datahost+API+'recruitingCEJobRequisitionDetails?'+urlencode(params))
    if status!=200:raise ValueError('Public Oracle job details are unavailable')
    return status,body
