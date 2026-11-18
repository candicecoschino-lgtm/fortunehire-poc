"""Keep bounded role-duty evidence from the description already being fetched.

Never use the whole page, company profile, benefits, or qualifications as duties.
Classification lives in the shared browser module; collection requires no AI/API.
"""
import re

START = re.compile(r'^(?:(?:key|primary|essential|major|core|job|position|role)\s+)*(?:responsibilities|duties|accountabilities|functions)|^what you(?:[’\']ll| will) (?:do|be doing)|^your (?:role|impact|responsibilities)|^in this role(?:[, :]|$)|^you will\s*[:：]?$', re.I)
STOP = re.compile(r'^(?:(?:required|preferred|basic|minimum|additional)\s+)*(?:qualifications|requirements|skills|experience|education)|^(?:what you (?:bring|need)|who you are|about (?:us|the company)|why (?:join|work)|benefits|compensation|salary|pay range|equal (?:employment|opportunity)|our (?:company|benefits|commitment)|application|accommodation)', re.I)
ACTION = re.compile(r'^(?:(?:you(?:[’\']ll| will)|this (?:role|position) (?:will|is responsible for))\s+|responsible for\s+)?(?:design|develop|build|maintain|manage|lead|deliver|provide|support|analy[sz]e|prepare|process|perform|coordinate|execute|implement|monitor|resolve|sell|drive|negotiate|recruit|administer|conduct|operate|repair|inspect|ensure|assist|create|oversee|evaluate|review|plan|schedule|greet|stock|serve|cook|test|write|respond|handle|advise|represent|optimi[sz]e|supervise|diagnose|treat|assess|dispense|weld|assemble)\w*\b', re.I)
BOILER = re.compile(r'\b(?:equal opportunity employer|reasonable accommodation|without regard to|we offer|our benefits|benefits package|health insurance|paid time off|401\(?k|all qualified applicants|employment eligibility|must be authorized|years of experience|bachelor.?s degree)\b', re.I)


def extract_function_context(description, source=None):
    active = False
    excluded = False
    duties = []
    for raw in description[:100000].splitlines():
        line = re.sub(r'\s+', ' ', raw).strip(' \t•*-–')
        if not line:
            continue
        # Headings and their inline text are handled independently.
        heading, sep, tail = line.partition(':')
        if STOP.match(heading):
            active = False
            excluded = True
            continue
        if START.match(heading):
            active = True
            excluded = False
            line = tail.strip() if sep else ''
        if excluded or not line or BOILER.search(line):
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
    return {'version': 1, 'duties': duties, 'category': category}
