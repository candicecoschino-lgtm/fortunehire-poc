"""Keep bounded role-duty evidence from the description already being fetched.

Never use the whole page, company profile, benefits, or qualifications as duties.
Classification lives in the shared browser module; collection requires no AI/API.
"""
import re

START = re.compile(r'^(?:(?:key|primary|essential|major|core|job|position|role)\s+)*(?:responsibilities|duties|accountabilities|functions)|^what you(?:[’\']ll| will) (?:do|be doing)|^your (?:role|impact|responsibilities)|^in this role(?:[, :]|$)|^you will\s*[:：]?$', re.I)
SKILLS = re.compile(r'^(?:(?:required|preferred|basic|minimum|additional)\s+)*(?:qualifications|requirements|skills|technical skills|experience|what you bring|what you need)\s*$', re.I)
STOP = re.compile(r'^(?:minimum education(?:/experience)? requirement|education(?: requirements?)?|about (?:us|the company)|why (?:join|work)|benefits|compensation|salary|pay(?: transparency| range| and benefits)?|hours per week|schedule|work schedule|shift(?: details)?|location(?: details| requirements)?|where you(?: will)? work|equal (?:employment|opportunity)|our (?:company|benefits|commitment)|application|accommodation|physical requirements|work authorization)', re.I)
ACTION = re.compile(r'^(?:(?:you(?:[’\']ll| will)|this (?:role|position) (?:will|is responsible for))\s+|responsible for\s+)?(?:design|develop|build|maintain|manage|lead|deliver|provide|support|analy[sz]e|prepare|process|perform|coordinate|execute|implement|monitor|resolve|sell|drive|negotiate|recruit|administer|conduct|operate|repair|inspect|ensure|assist|create|oversee|evaluate|review|plan|schedule|greet|stock|serve|cook|test|write|respond|handle|advise|represent|optimi[sz]e|supervise|diagnose|treat|assess|dispense|weld|assemble|facilitate|establish|identify|reconcile|draft|interpret|code|forecast|dispatch|calculate|collaborate|integrate|configure|troubleshoot|formulate|recommend|research|track|partner|document|qualify|validate|install|certify|mentor|train|present|prioritize|innovate)\w*\b', re.I)
BOILER = re.compile(r'\b(?:equal opportunity employer|reasonable accommodation|without regard to|we offer|our benefits|benefits package|health insurance|paid time off|401\(?k|all qualified applicants|employment eligibility|must be authorized|years of experience|bachelor.?s degree)\b', re.I)
SKILL_NOISE = re.compile(r'\b(?:degree|diploma|education|hours per week|pay transparency|salary range|pay range|shift|work location|relocation assistance|authorized to work|employment visa|accommodation|equal opportunity|years? of experience|minimum\s+\d+\+?\s+years?\s+(?:of\s+)?relevant experience)\b', re.I)
SHORT_SKILL = re.compile(r'^(?:AI|ML|R|SQL|Python|Java|JavaScript|C\+\+|C#|AWS|GCP|Azure|SAP|ERP|CRM|HIPAA|OSHA|PMP|CPA|CFA|RN|LPN|ACLS|BLS|SIEM|SOC|NLP|ETL|GIS|Tableau|Power ?BI|TensorFlow|PyTorch|Spark|pandas|SAS|React|Node\.js|Linux|Cisco|Kubernetes)$', re.I)


def extract_function_context(description, source=None):
    active = False
    skill_active = False
    excluded = False
    duties = []
    required_skills = []
    preferred_skills = []
    preferred = False
    for raw in description[:100000].splitlines():
        line = re.sub(r'\s+', ' ', raw).strip(' \t•*-–')
        if not line:
            continue
        # Headings and their inline text are handled independently.
        heading, sep, tail = line.partition(':')
        if STOP.match(heading):
            active = False
            skill_active = False
            excluded = True
            continue
        if SKILLS.match(heading):
            active = False
            skill_active = True
            excluded = False
            preferred = bool(re.match(r'preferred|desired', heading, re.I))
            line = tail.strip() if sep else ''
        if START.match(heading):
            active = True
            skill_active = False
            excluded = False
            line = tail.strip() if sep else ''
        if excluded or not line or BOILER.search(line):
            continue
        if skill_active:
            if SKILL_NOISE.search(line):
                continue
            for sentence in re.split(r'(?<=[.!?;])\s+|\s*,\s*', line):
                sentence = sentence.strip(' •*-–')
                if 2 <= len(sentence) <= 500 and (len(sentence) >= 12 or SHORT_SKILL.fullmatch(sentence.rstrip('.'))) and not SKILL_NOISE.search(sentence):
                    target = preferred_skills if preferred else required_skills
                    if sentence not in target and len(target) < 16:
                        target.append(sentence)
            continue
        for sentence in re.split(r'(?<=[.!?;])\s+', line):
            sentence = sentence.strip(' •*-–')
            if ACTION.match(sentence) and (active or re.match(r'^(?:you(?:[’\']ll| will)|responsible for|this (?:role|position))\b', sentence, re.I)):
                # Do not cut a sentence into apparently unrelated evidence.
                if 15 <= len(sentence) <= 500 and sentence not in duties:
                    duties.append(sentence)
            if len(duties) == 16:
                break
        if len(duties) == 16:
            break
    source = source or {}
    category = source.get('occupationalCategory') or source.get('department') or ''
    if isinstance(category, dict):
        category = category.get('name', '')
    if not isinstance(category, str):
        category = ''
    category = re.sub(r'\s+', ' ', category).strip()[:120]
    return {'version': 2, 'duties': duties, 'requiredSkills': required_skills[:16], 'preferredSkills': preferred_skills[:16], 'category': category}
