"""Meta's advertised public job sitemap and matched individual posting data."""
import json,re,html
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit
from employer_adapters import Document
HOST='www.metacareers.com';SITEMAP='https://'+HOST+'/jobsearch/sitemap.xml'
def role_id(url):
 p=urlsplit(url);m=re.fullmatch(r'/profile/job_details/(\d+)/?',p.path)
 return m[1] if p.scheme=='https' and p.netloc==HOST and not p.query and not p.fragment and m else None
def discover(client):
 if SITEMAP not in (client.robots.site_maps() or []):raise ValueError('Meta job sitemap is no longer advertised')
 status,body=client.get(SITEMAP)
 if status!=200:raise ValueError('Meta public job sitemap unavailable')
 root=ET.fromstring(body);ns='{http://www.sitemaps.org/schemas/sitemap/0.9}'
 if root.tag!=ns+'urlset':raise ValueError('Unexpected Meta job sitemap format')
 found={}
 for entry in root.findall(ns+'url'):
  url=entry.findtext(ns+'loc') or '';req=role_id(url)
  if req:found[req]=url
 if not found or len(found)>10000:raise ValueError('Unexpected Meta job sitemap size')
 # All sitemap lastmod values can change together; none is a posting date.
 client.discovery_dates={};client.discovery_limited=False;client.discovery_warnings=[]
 return found
def enrich(source,body,url):
 req=role_id(url)
 if not req or source.get('hiringOrganization',{}).get('name')!='Meta':raise ValueError('Unexpected Meta posting identity')
 records=[]
 def walk(value):
  if isinstance(value,dict):
   record=value.get('xcp_requisition_job_description')
   if isinstance(record,dict):records.append(record)
   for child in value.values():walk(child)
  elif isinstance(value,list):
   for child in value:walk(child)
 for node in Document(body).nodes:
  if node['tag']=='script' and node['attrs'].get('type')=='application/json':
   try:walk(json.loads(''.join(x for x in node['children'] if isinstance(x,str))))
   except ValueError:continue
 if len(records)!=1 or records[0].get('id')!=req or records[0].get('title')!=source.get('title'):raise ValueError('Conflicting Meta individual role details')
 result=dict(source);parts=[str(source.get('description',''))]
 for field in ['responsibilities','qualifications']:
  value=source.get(field)
  if isinstance(value,str):parts.append(value)
 # Compensation remains quoted employer text until base-pay components and
 # geographic applicability support numerical filtering; no inferred salary.
 for row in records[0].get('public_compensation',[]):
  if not isinstance(row,dict) or row.get('country_code')!='US':continue
  low=row.get('compensation_amount_minimum','');high=row.get('compensation_amount_maximum','')
  if all(isinstance(v,str) and re.fullmatch(r'\$[\d,]+(?:\.\d{1,2})?/(?:year|hour)',v) for v in [low,high]):
   parts.append('<p>Employer-published U.S. compensation: '+html.escape(low+' – '+high)+'.</p>')
 result['description']='\n'.join(parts);result['_adapter']='meta-public-jobposting-and-matched-details'
 return result


def discovery_order(found,previous,now):
    """First-observed times prioritize new URLs; only JobPosting dates publish jobs."""
    from datetime import datetime
    result={}
    for req in found:
        value=previous.get(req)
        try:
            stamp=datetime.fromisoformat(value)
            if stamp.tzinfo is None or stamp>now:raise ValueError('Invalid observation time')
        except (ValueError,TypeError):value=now.isoformat()
        result[req]=value
    return result
