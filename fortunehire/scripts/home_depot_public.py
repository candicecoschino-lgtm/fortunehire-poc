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


def enrich(source,body,url=None):
    """Preserve matched role sections which the employer omits from JSON-LD."""
    import html
    from employer_adapters import Document,text
    doc=Document(body);identity=doc.find(id='gtm-jobdetail-idSC')
    value=source.get('identifier',{});req=str(value.get('value','') if isinstance(value,dict) else value)
    result=dict(source)
    # The country schema does not establish all-state eligibility: the role's
    # Remote/virtual explanation can require commuting to an assigned office.
    result.pop('applicantLocationRequirements',None)
    # The page's current_job record must match this posting and requisition.
    records=[]
    for node in doc.nodes:
        if node['tag']!='script':continue
        script=''.join(part for part in node['children'] if isinstance(part,str)).strip()
        match=re.match(r'var\s+current_job\s*=\s*',script)
        if not match:continue
        try:record,end=json.JSONDecoder().raw_decode(script[match.end():])
        except (ValueError,TypeError):continue
        if script[match.end()+end:].strip() not in ('',';'):continue
        if not isinstance(record,dict):continue
        target=urlsplit(url or result.get('url',''))
        path=target.path.strip('/').split('/')
        if len(path)<2 or str(record.get('id',''))!=path[1] or str(record.get('ref',''))!=req or record.get('scout_orgid')!=1814:continue
        records.append(record)
    if len(records)==1 and isinstance(records[0].get('employment_type'),str) and records[0]['employment_type'].strip():
        result['employmentType']=records[0]['employment_type']
        result['_employmentTypeEvidence']='Employer matched Home Depot employment_type='+records[0]['employment_type']
    if not identity:return result
    if text(identity).strip()!=req:raise ValueError('Conflicting Home Depot role-section requisition')
    def section(anchor,label):
        target=doc.find(id=anchor)
        if not target:return ''
        for parent in [doc.root]+doc.nodes:
            children=[v for v in parent['children'] if isinstance(v,dict)]
            for i,node in enumerate(children[:-1]):
                if node is target:
                    row=children[i+1]
                    if 'fusion-builder-row-inner' not in row['attrs'].get('class','').split():return ''
                    headings=[]
                    def walk(n):
                        if not isinstance(n,dict):return
                        if n['tag']=='h2':headings.append(re.sub(r'\s+',' ',text(n)).strip())
                        for child in n['children']:walk(child)
                    walk(row)
                    if headings!=[label]:return ''
                    return re.sub(r'\s+',' ',text(row)).strip()
        return ''
    pay=section('payrange','Pay Range');work=section('worklocation','Work Location')
    if pay:pay=re.sub(r'(\$[\d,.]+)\s*\ufffd\s*(?=\$[\d,.]+)',r'\1 – ',pay)
    parts=[str(result.get('description',''))]
    for value in [pay,work]:
        if value:parts.append('<p>'+html.escape(value)+'</p>')
    result['description']='\n'.join(parts);result['_adapter']='home-depot-matched-role-and-sections'
    if work:
        label=re.sub(r'^Work Location\s*','',work)
        match=re.match(r'(Remote/virtual|Onsite|On-site|Hybrid)\b',label,re.I)
        if match:
            result['jobLocationType']={'remote/virtual':'REMOTE','onsite':'ON_SITE','on-site':'ON_SITE','hybrid':'HYBRID'}[match[1].lower()]
            result['_homeDepotWorksite']=work
    return result
