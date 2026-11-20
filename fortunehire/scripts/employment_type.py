"""Keep employment type unspecified unless the employer's role evidence supports it."""
import re

SPACE=r'[\s\u2010-\u2015_-]*'
def title_employment(title):
 for pattern,kind in [
  (r'\bpart'+SPACE+r'time\b','Part-time'),
  (r'\bintern(?:ship)?\b','Internship'),
  (r'\bfull'+SPACE+r'time\b','Full-time'),
  (r'\b(?:temporary|seasonal)\b','Temporary'),
  (r'[\[(]\s*contract(?:or)?\s*[\])]|\s[-\u2010-\u2015]\s*contract(?:or)?\s*$','Contract')]:
  match=re.search(pattern,title,re.I)
  if match:return kind,'Employer job title explicitly states '+match[0].strip()+'.'
 return 'Not specified',''

def resolve_employment(title,description,current='Not specified',raw_type=''):
 kind,evidence=title_employment(title)
 if kind=='Part-time':return kind,evidence # Existing user-selected title priority.
 if current!='Not specified':return current,''
 if kind!='Not specified':return kind,evidence
 ambiguous=bool(re.search(r'\bfull'+SPACE+r'time\b',raw_type,re.I) and re.search(r'\bpart'+SPACE+r'time\b',raw_type,re.I))
 for pattern,kind in [(r'full'+SPACE+r'time','Full-time'),(r'part'+SPACE+r'time','Part-time'),(r'contract(?:or)?','Contract'),(r'temporary','Temporary'),(r'intern(?:ship)?','Internship')]:
  if not ambiguous and re.search(r'\b'+pattern+r'\b',raw_type,re.I):return kind,'Employer employmentType explicitly states '+raw_type+'.'
  label=re.search(r'\b(?:time type|employment type|employment status|job schedule|work schedule|position type)\s*:\s*('+pattern+r')\b',description,re.I)
  declaration=re.search(r'\b(?:this|the)\s+(?:(?:position|role|job)\s+(?:is|will be)\s+(?:an?\s+)?(?:regular\s+)?|is\s+(?:an?\s+)?(?:regular\s+)?)('+pattern+r')\s*(?:role|position|job|employment|opportunity)?\b',description,re.I)
  match=label or declaration
  if match:
   following=description[match.end():match.end()+60]
   if re.match(r'\s*(?:or|and|/)\s*(?:full[\s-]*time|part[\s-]*time)',following,re.I):continue
   return kind,'Employer role description: '+match[0]+'.'
 return current,''

def apply_employment_policy(job):
 current='Not specified' if job.get('employmentTypeBasis')=='assumed-full-time' else job['employmentType']
 kind,evidence=resolve_employment(job['title'],'',current)
 if kind=='Not specified':
  if job.get('employmentTypeBasis')!='assumed-full-time':return job
  result={k:v for k,v in job.items() if k not in ('employmentTypeBasis','employmentTypeNote')}
  return {**result,'employmentType':'Not specified'}
 if kind==job['employmentType'] and not job.get('employmentTypeBasis'):return job
 result={k:v for k,v in job.items() if k not in ('employmentTypeBasis','employmentTypeNote')}
 return {**result,'employmentType':kind,'evidence':{**job.get('evidence',{}),**({'employmentType':evidence} if evidence else {})}}
