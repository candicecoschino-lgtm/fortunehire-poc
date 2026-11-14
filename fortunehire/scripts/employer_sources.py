"""Bounded public search interfaces explicitly linked by the employer portals."""
import json
from urllib.parse import urlencode, urlsplit

ORACLE = {
    'enterpriseplatform.dell.com': ('enterpriseplatform.dell.com','CX_1001','/hcmUI/CandidateExperience/en/sites/CX_1001'),
    'www.krogerfamilycareers.com': ('eluq.fa.us2.oraclecloud.com','CX_2001','/en/sites/CX_2001'),
}
API='/hcmRestApi/resources/11.13.18.05/'

def public_search(client, client_factory):
    """Inspect at most 60 recent results; publishing still checks each job."""
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
