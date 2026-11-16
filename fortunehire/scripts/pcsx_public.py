"""Reviewed employer-owned PCSX portals: public search, role page and role API."""
import json,re,html
from datetime import datetime,timezone
from urllib.parse import urlsplit,urlencode
from employer_adapters import Document
CONFIG={'apply.careers.microsoft.com':('microsoft.com','microsoft'),'jobs.nvidia.com':('nvidia.com','nvidia')}
US=('US','USA','United States','United States of America')
def payload(body):
    value=json.loads(body)
    if value.get('status')!=200 or value.get('error',{}).get('message') or not isinstance(value.get('data'),dict):raise ValueError('Invalid employer public job response')
    return value['data']
def role_id(url,host):
    p=urlsplit(url);m=re.fullmatch(r'/careers/job/(\d+)',p.path)
    return m[1] if p.scheme=='https' and p.netloc==host and not p.query and not p.fragment and m else None
def raw_locations(row):
    result=[]
    for value in row.get('locations',[]):
        if not isinstance(value,str):continue
        parts=[part.strip() for part in value.split(',',2)]
        if len(parts)==3 and parts[0] in US and parts[1] and parts[2] and parts[1].casefold()!='multiple locations':result.append(parts)
    return result
def discover(client):
    host=client.host;domain,company=CONFIG[host];found={};dates={};total=0
    for start in (0,10,20,30,40,50):
        params={'domain':domain,'query':'','location':'United States','start':start,'sort_by':'timestamp','filter_include_remote':1}
        status,body=client.get('https://'+host+'/api/pcsx/search?'+urlencode(params))
        if status!=200:raise ValueError('Employer public job search unavailable')
        data=payload(body);rows=data.get('positions');total=data.get('count',0)
        if not isinstance(rows,list):raise ValueError('Missing employer public positions')
        for row in rows:
            req=str(row.get('id',''));path=row.get('positionUrl','')
            if not req.isdigit() or role_id('https://'+host+path,host)!=req or not raw_locations(row):continue
            found[req]='https://'+host+path
            stamp=row.get('postedTs')
            if isinstance(stamp,(int,float)) and not isinstance(stamp,bool):
                try:dates[req]=datetime.fromtimestamp(stamp,timezone.utc).date().isoformat()
                except (ValueError,OverflowError,OSError):pass
        if len(found)>=20 or len(rows)<10:break
    client.discovery_dates=dates;client.discovery_limited=total>len(found);client.discovery_warnings=[]
    return found
def work_setting(data,company):
    if company=='microsoft':
        values=data.get('efcustomTextWorkSite',[])
        label=values[0] if isinstance(values,list) and len(values)==1 and isinstance(values[0],str) else ''
        clean=label.lower();match=re.match(r'^([0-5]) days?\s*/\s*week in-office\b',clean)
        if match:
            days=int(match[1]);return ('REMOTE' if days==0 else 'ON_SITE' if days==5 else 'HYBRID'),label
        if clean=='fully on-site':return 'ON_SITE',label
        return '',label
    if data.get('workLocationOption')=='remote':return 'REMOTE','Employer job location type: Remote'
    # An Office search category does not establish a full-time on-site schedule.
    return '',''
def enrich(body,details,url,host):
    req=role_id(url,host);data=payload(details);domain,company=CONFIG[host]
    if not req or str(data.get('id',''))!=req or role_id(data.get('publicUrl',''),host)!=req or data.get('positionUrl')!='/careers/job/'+req:raise ValueError('Conflicting employer public posting identity')
    ats=str(data.get('atsJobId',''));display=str(data.get('displayJobId',''))
    if not ats or ats!=display:raise ValueError('Conflicting employer requisition identity')
    jobs=[]
    for node in Document(body).nodes:
        if node['tag']=='script' and node['attrs'].get('type','').lower()=='application/ld+json':
            value=json.loads(''.join(v for v in node['children'] if isinstance(v,str)))
            if isinstance(value,dict) and value.get('@type')=='JobPosting':jobs.append(value)
    if len(jobs)!=1:raise ValueError('Missing matching employer individual JobPosting')
    source=jobs[0]
    if role_id(source.get('url',''),host)!=req or html.unescape(source.get('title','')).strip()!=html.unescape(data.get('name','')).strip():raise ValueError('Conflicting employer role title or URL')
    stamp=data.get('postedTs')
    if not isinstance(stamp,(int,float)) or isinstance(stamp,bool):raise ValueError('Missing employer posting timestamp')
    date=datetime.fromtimestamp(stamp,timezone.utc).date().isoformat()
    if str(source.get('datePosted',''))[:10]!=date:raise ValueError('Conflicting employer posting dates')
    description=data.get('jobDescription')
    if not isinstance(description,str) or not description.strip():raise ValueError('Missing employer job description')
    locations=raw_locations(data);model,label=work_setting(data,company)
    source.update(identifier={'value':ats},description=description,jobLocation=[{'address':{'addressCountry':country,'addressRegion':state,'addressLocality':city}} for country,state,city in locations],_adapter='employer-pcsx-page-and-public-details',_pcsxWorksite=label)
    source.pop('validThrough',None) # The portal's generic six-month schema validity is not a verified closing deadline.
    source.pop('jobLocationType',None);source.pop('applicantLocationRequirements',None)
    if model:source['jobLocationType']=model
    if model=='REMOTE':source['applicantLocationRequirements']=[{'@type':'AdministrativeArea','name':state} for country,state,city in locations if re.fullmatch(r'Remote',city,re.I)]
    if company=='microsoft':
        values=data.get('efcustomTextRequiredTravel',[])
        if isinstance(values,list) and len(values)==1 and isinstance(values[0],str):
            label=values[0];m=re.fullmatch(r'(?:Less than\s+|Up to\s+)?(\d{1,3})(?:\s*-\s*(\d{1,3}))?\s*%',label,re.I)
            if m and 0<=int(m[1])<=int(m[2] or m[1])<=100:source.update(_pcsxTravel=int(m[2] or m[1])>0,_pcsxTravelLabel=label)
    return '<script type="application/ld+json">'+json.dumps(source).replace('<','\\u003c')+'</script>'
def fetch(client,url,body):
    host=client.host;domain,company=CONFIG[host];req=role_id(url,host)
    if not req:raise ValueError('Invalid employer public job URL')
    status,details=client.get('https://'+host+'/api/pcsx/position_details?'+urlencode({'position_id':req,'domain':domain,'hl':'en'}))
    if status in (404,410):return status,''
    if status!=200:raise ValueError('Employer public role details unavailable')
    if json.loads(details).get('status') in (404,410):return 404,''
    return 200,enrich(body,details,url,host)
