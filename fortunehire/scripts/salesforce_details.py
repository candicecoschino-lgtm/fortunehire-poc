"""Cross-check public Workday role details against the individual JobPosting."""
import json,re,html
from urllib.parse import urlsplit
from employer_adapters import Document
HOST='salesforce.wd12.myworkdayjobs.com'
def enrich(body,details):
    sources=[]
    for node in Document(body).nodes:
        if node['tag']=='script' and node['attrs'].get('type')=='application/ld+json':
            value=json.loads(''.join(x for x in node['children'] if isinstance(x,str)))
            if isinstance(value,dict) and value.get('@type')=='JobPosting':sources.append(value)
    if len(sources)!=1:raise ValueError('Missing matching Salesforce JobPosting')
    source=sources[0];info=json.loads(details).get('jobPostingInfo',{})
    req=source.get('identifier',{}).get('value')
    if not req or info.get('jobReqId')!=req or info.get('jobPostingSiteId')!='External_Career_Site':raise ValueError('Conflicting Salesforce role identity')
    if not re.fullmatch(r'.+_'+re.escape(req)+r'(?:-\d+)?',info.get('jobPostingId','')):raise ValueError('Conflicting Salesforce posting ID')
    link=urlsplit(info.get('externalUrl',''))
    if link.scheme!='https' or link.netloc!=HOST or not re.search(r'_'+re.escape(req)+r'(?:-\d+)?$',link.path):raise ValueError('Unexpected Salesforce application URL')
    if html.unescape(source.get('title','')).strip()!=html.unescape(info.get('title','')).strip() or str(source.get('datePosted',''))[:10]!=str(info.get('startDate',''))[:10]:raise ValueError('Conflicting Salesforce title or posting date')
    if not isinstance(info.get('posted'),bool) or not isinstance(info.get('canApply'),bool):raise ValueError('Missing Salesforce publication status')
    country=info.get('country',{}).get('descriptor')
    if country not in ('US','USA','United States','United States of America'):raise ValueError('Not a verified U.S. Salesforce role')
    locations=[info.get('location')]+info.get('additionalLocations',[])
    if not locations or any(not isinstance(v,str) or not v.strip() for v in locations):raise ValueError('Missing Salesforce role locations')
    source.update(url=info['externalUrl'],jobLocation=[{'address':{'addressCountry':country,'addressLocality':loc}} for loc in dict.fromkeys(locations)],description=info.get('jobDescription',''),_salesforceRemoteType=info.get('remoteType',''),_employerClosed=not info['posted'] or not info['canApply'],_adapter='salesforce-public-role-details')
    return '<script type="application/ld+json">'+json.dumps(source).replace('<','\\u003c')+'</script>'
