"""User-selected fallback after employer statements and U.S. geography validation."""
import re

LOCATION_BASIS='listed-location'
LOCATION_REASON='On-site classification based on the employer-listed city/state; the employer did not state a work arrangement.'

def use_listed_location(arrangement,locations,evidence=''):
    if arrangement!='unknown' or evidence or not locations:return False
    for location in locations:
        city=location.get('city','').strip();state=location.get('state','').strip()
        if not city or not state:return False
        if city.casefold()==state.casefold() and state!='New York':return False
        if re.search(r'\b(?:remote|virtual|multiple|various|nationwide|anywhere)\b',city,re.I):return False
        if re.fullmatch(r'(?:US|USA|United States(?: of America)?|all(?: locations)?|home(?: office| based)?|not specified|not available|unknown|unspecified|n/?a)',city,re.I):return False
    return True

def apply_location_policy(job):
    if job.get('arrangementReviewRequired'):return job
    if job['arrangement']=='unknown' and not job.get('evidence',{}).get('arrangement') and job.get('companyId') not in ('salesforce','microsoft','nvidia'):
        remote_states=sorted({location['state'] for location in job['locations'] if location['city'].strip().casefold()=='remote'})
        if remote_states:
            return {**job,'arrangement':'remote','remoteScope':'states','eligibleStates':remote_states,'locationNote':'Remote in '+', '.join(remote_states)+'; employer-listed locations: '+job['locationNote'],'evidence':{**job.get('evidence',{}),'arrangement':'Employer-listed job location is Remote; eligibility is limited to its named states.'}}
    if not use_listed_location(job['arrangement'],job['locations'],job.get('evidence',{}).get('arrangement','')):return job
    # Keep the employer-evidence object and real check dates intact. This is
    # a disclosed classification policy, not an employer worksite statement.
    return {**job,'arrangement':'on-site','arrangementBasis':LOCATION_BASIS,'arrangementNote':LOCATION_REASON}
