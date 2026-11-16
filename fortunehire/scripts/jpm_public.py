"""Draft: user-approved JPMorgan public-job scope, never applicant APIs."""
import re,time,urllib.error
from urllib.parse import urlsplit,parse_qs
HOST='jpmc.fa.oraclecloud.com'
BASE='/hcmUI/CandidateExperience/en/sites/CX_1001'
API='/hcmRestApi/resources/11.13.18.05/'
def allowed(url):
 p=urlsplit(url)
 if p.scheme!='https' or p.netloc!=HOST or p.fragment:return False
 if p.path=='/robots.txt':return not p.query
 if p.path in (BASE+'/requisitions',BASE+'/jobs') or re.fullmatch(re.escape(BASE)+r'/job/\d+/?',p.path):return not p.query
 q=parse_qs(p.query)
 if set(q)!={'onlyData','expand','finder'} or any(len(v)!=1 for v in q.values()) or q['onlyData']!=['true']:return False
 if p.path==API+'recruitingCEJobRequisitions':return q['expand']==['requisitionList'] and bool(re.fullmatch(r'findReqs;siteNumber=CX_1001,limit=20,offset=(?:0|20|40),sortBy=POSTING_DATES_DESC',q['finder'][0]))
 if p.path==API+'recruitingCEJobRequisitionDetails':return q['expand']==['workLocation,otherWorkLocations,secondaryLocations'] and bool(re.fullmatch(r'ById;siteNumber=CX_1001,Id=\d+',q['finder'][0]))
 return False
def create(base_client,error_type,approved=False):
 from crawler_rules import CrawlerRules
 class PublicJobsClient(base_client):
  def __init__(self,host):
   if host!=HOST:raise error_type('Unexpected approved source host')
   try:super().__init__(host,delay=2)
   except error_type as e:
    cause=e.__cause__
    if not approved or not isinstance(cause,urllib.error.HTTPError) or cause.code!=403 or cause.url!='https://'+HOST+'/robots.txt':raise
    self.robots=CrawlerRules();self.robots.parse([])
   self.last=time.monotonic()
  def get(self,url,check=True):
   if not allowed(url):raise error_type('Outside approved public-job scope')
   status,body=super().get(url,check=check)
   if re.search(r'awswaf|not a robot|verify.{0,70}human',body,re.I):raise error_type('Employer verification challenge; collection stopped')
   return status,body
 return PublicJobsClient(HOST)
