"""Home Depot's credential-free, employer-published search interface."""
import json,re
from urllib.parse import urlencode,urlsplit
COMPANY='companies/8454851f-07b7-4e4c-9b5f-00e0ffbfcb09'
PORTALS=('THD-GH-Construction','THD-GH-Bell','THD-GH-Umi','THD-GH-Cancostile','THD-GH-Jarrell','THD-GH-MVP','THD-GH-Victoria','KBR-5032','Workday','Paycom')
def search_data(body):
    prefix='CWS.jobs.jobCallback('
    if not body.startswith(prefix):raise ValueError('Unexpected Home Depot public response')
    data,end=json.JSONDecoder().raw_decode(body[len(prefix):])
    if body[len(prefix)+end:].strip() not in (')',');') or not isinstance(data,dict) or not isinstance(data.get('searchResults'),list):raise ValueError('Invalid Home Depot public job data')
    return data
def discover(client,client_factory):
    api=client_factory('jobsapi-google.m-cloud.io')
    params={'callback':'CWS.jobs.jobCallback','pageSize':20,'offset':0,'companyName':COMPANY,'customAttributeFilter':'('+' OR '.join('ats_portalid="'+v+'"' for v in PORTALS)+')','orderBy':'posting_publish_time desc'}
    status,body=api.get('https://jobsapi-google.m-cloud.io/api/job/search?'+urlencode(params))
    if status!=200:raise ValueError('Home Depot public search unavailable')
    data=search_data(body);found={};dates={}
    for entry in data['searchResults'][:20]:
        row=entry.get('job',{});req=str(row.get('id',''));url=row.get('url','');p=urlsplit(url)
        if row.get('scout_orgid')!=1814 or row.get('primary_country')!='US' or not req.isdigit() or p.scheme!='https' or p.netloc!=client.host or p.query or p.fragment or not re.fullmatch(r'/job/'+re.escape(req)+r'/[^/]+/?',p.path):continue
        found[req]=url;dates[req]=str(row.get('open_date',''))[:10]
    client.discovery_dates=dates;client.discovery_limited=data.get('totalHits',0)>len(found);client.discovery_warnings=[]
    return found
