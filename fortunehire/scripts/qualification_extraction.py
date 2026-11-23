"""Offline qualification evidence extraction for already-authorized postings.

This module neither fetches nor publishes data. Pass the verified employer
record, preserving its dedicated fields where the upstream format has them.
"""

from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
import re
from typing import Literal
from unicodedata import normalize
from urllib.parse import urlsplit


Kind = Literal['required', 'preferred', 'ambiguous']
Confidence = Literal['high', 'medium']
KINDS = ('required', 'preferred', 'ambiguous')


@dataclass(frozen=True)
class Evidence:
    text: str
    kind: Kind
    types: tuple[str, ...]
    source_url: str
    source_field: str
    section: str | None
    block: int
    confidence: Confidence


@dataclass(frozen=True)
class Extraction:
    evidence: tuple[Evidence, ...]
    omitted: dict[str, int]


# Only reviewed fields whose names convey qualification scope. Unknown employer
# fields should be mapped explicitly at the adapter boundary.
DEDICATED_FIELDS = {
    'requiredQualifications': 'required',
    'minimumQualifications': 'required',
    'basicQualifications': 'required',
    'requiredSkills': 'required',
    'educationRequirements': 'required',
    'experienceRequirements': 'required',
    'preferredQualifications': 'preferred',
    'desiredQualifications': 'preferred',
    'optionalQualifications': 'preferred',
    'preferredSkills': 'preferred',
    'qualifications': 'ambiguous',
    'ExternalQualificationsStr': 'ambiguous',
    'reqlistitem.qualification': 'ambiguous',
}

BLOCK_TAGS = {
    'article', 'aside', 'blockquote', 'br', 'dd', 'div', 'dl', 'dt', 'footer',
    'header', 'li', 'ol', 'p', 'section', 'table', 'td', 'tr', 'ul',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
}
HIDDEN_TAGS = {'script', 'style', 'template', 'noscript'}
LIST_ITEM = re.compile(r'^\s*(?:[•●▪◦‣*]|[-–—](?=\s)|\d+[.)](?=\s))\s*')
SPACE = re.compile(r'\s+')
FORMAT_MARKS = str.maketrans('', '', '\u200b\u200c\u200d\ufeff\u200e\u200f')


class DescriptionBlocks(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.blocks = []
        self.hidden = []
        self.list_depth = 0
        self.list_path = []
        self.next_list = 0
        self.feed(html)
        self.close()
        self.flush()

    def flush(self):
        value = SPACE.sub(' ', ''.join(self.parts)).strip()
        if value:
            self.blocks.append((value, tuple(self.list_path)))
        self.parts.clear()

    def handle_starttag(self, tag, attrs):
        if tag in HIDDEN_TAGS:
            self.hidden.append(tag)
        if self.hidden:
            return
        if tag in ('ul', 'ol'):
            self.flush()
            self.next_list += 1
            self.list_path.append(self.next_list)
        elif tag == 'li':
            self.flush()
            self.list_depth += 1
        elif tag in BLOCK_TAGS and not self.list_depth:
            self.flush()
        elif tag == 'br' or self.list_depth and tag in BLOCK_TAGS:
            self.parts.append(' ')

    def handle_endtag(self, tag):
        if self.hidden:
            if self.hidden[-1] == tag:
                self.hidden.pop()
            return
        if tag in ('ul', 'ol'):
            self.flush()
            if self.list_path:
                self.list_path.pop()
        elif tag == 'li':
            self.flush()
            self.list_depth = max(0, self.list_depth - 1)
        elif tag in BLOCK_TAGS and not self.list_depth:
            self.flush()
        elif self.list_depth and tag in BLOCK_TAGS:
            self.parts.append(' ')

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


HTML_TAG = re.compile(r'</?(?:h[1-6]|p|div|li|ul|ol|br|strong|b|span|section|script|style|table)\b', re.I)


def description_blocks(value):
    if not isinstance(value, str):
        return []
    html = value if HTML_TAG.search(value) else unescape(value)
    if HTML_TAG.search(html):
        return DescriptionBlocks(html).blocks
    return [(line.strip(), None) for line in html.splitlines() if line.strip()]


def positioned_blocks(value):
    if isinstance(value, (tuple, list)):
        for item in value:
            yield from positioned_blocks(item)
    elif isinstance(value, dict):
        # Preserve the provider's own prose; do not stringify schema objects or
        # synthesize text for machine-only values.
        for key in ('description', 'text', 'name', 'credentialCategory'):
            if isinstance(value.get(key), str) and value[key].strip():
                yield from description_blocks(value[key])
                break
    else:
        yield from description_blocks(value)


def field_blocks(value):
    """Yield the source blocks in their provenance order for offline review."""
    return (text for text, _ in positioned_blocks(value))


QUAL = r'(?:qualifications?|requirements?|(?:technical )?skills?(?:\s*(?:and|&|/)\s*(?:experience|abilities))?|education(?:\s+and\s+experience)?|experience)'
REQUIRED_HEADING = re.compile(
    rf'(?:(?:(?:additional|job|role|position) )?(?:required|minimum|basic|mandatory|essential|critical)(?: required)? {QUAL}'
    r'|(?:job|position|minimum) requirements?(?: we seek)?|minimum qualifications and requirements'
    r'|minimum education/experience requirements?|required field of study|your skills (?:and|&) abilities \(required qualifications\)'
    r'|what(?:[’\']s| is) needed to succeed \(minimum qualifications\)'
    r'|(?:basic|minimum|required) (?:qualifications?|requirements?) \(required skills\s*(?:/| and )\s*experience\)'
    r'|what you(?:[’\']ll| will) need(?: to have)?|what you need to succeed'
    r'|you(?:[’\']ll| will) (?:have|need)(?: (?:the following|to have))?|required|requirements)', re.I,
)
PREFERRED_HEADING = re.compile(
    rf'(?:(?:additional )?(?:preferred|desired|desirable|optional) {QUAL}|preferred(?: qualifications?)?'
    r'|nice[- ]to[- ]have|desired|optional|bonus points|what sets you apart|desired characteristics(?: and eligibility| & eligibility)?'
    r'|even better(?:,)? (?:if you have|you may have)|it[’\']d be great if you (?:also )?have'
    r'|preferred skills\s*/\s*certifications?|preferred qualifications \(desired skills\s*(?:/| and )\s*experience\)'
    r'|what will give you a competitive edge \(preferred (?:qualifications|skills)\)'
    r'|your skills (?:and|&) abilities \(preferred qualifications\))', re.I,
)
AMBIGUOUS_HEADING = re.compile(
    rf'(?:{QUAL}|qualifications\s*(?:/|and)\s*requirements|requirements and qualifications'
    r'|(?:additional|other) (?:job |eligibility )?requirements?'
    r'|education and experience requirements?|your skills (?:and|&) abilities \(qualifications\)'
    r'|physical requirements|work authorization|security clearance|export control requirements|visa sponsorship'
    r'|you might thrive in this role if you|what makes you a great fit|ideal candidate profile|skills and competencies'
    r'|relevant work experience|certifications? \(if applicable\)'
    r'|about you|who you are|what we(?:[’\']re| are) looking for|what we expect'
    r'|what you(?:(?:[’\']ll| will) bring| bring))', re.I,
)
BOUNDARY = re.compile(
    r'^(?:(?:about (?:us|the company|the team|the role|the job|[A-Z][\w -]+)|who we are|company (?:overview|description)'
    r'|(?:key |primary |essential |position |job |role )*(?:responsibilities|duties|accountabilities)'
    r'|(?:the )?role overview|job (?:description|summary)|position summary|work environment|working conditions'
    r'|(?:physical|travel|location|worksite) requirements|compensation(?: and benefits)?|pay(?: transparency| range)?'
    r'|salary(?: range)?|benefits(?: and perks)?|what we offer|why (?:join|work)|how to apply'
    r'|equal (?:employment|opportunity)|accommodations?|legal (?:notice|disclaimer)|additional information'
    r'|schedule|shift|relocation(?: assistance)?|employment type|job category|application (?:deadline|process)'
    r'|drug[- ]free workplace|(?:primary|job) location|disclaimer|logistics|what success looks like'
    r'|perks and benefits|employees at all levels are expected to|other duties)\b'
    r'|what you(?:[’\']ll| will) (?:do|be doing|work on)\b)', re.I,
)
FOOTER = re.compile(
    r'^(?:you may not check every box|if you (?:do not|don[’\']t) meet (?:all|every)|we encourage you to apply'
    r'|as an established global company|we offer\b|we are (?:an equal opportunity|committed to)'
    r'|(?:the |our )?(?:base )?(?:compensation|salary|pay) range\b|for (?:more )?information (?:about|on) (?:benefits|pay)'
    r'|joining our team comes with|at .{1,30} we (?:offer|strive to deliver)\b|employee discounts?\b'
    r'|this posting is expected to remain open|medical/dental/vision coverage'
    r'|our .{1,80} jobs earn between|ready to develop .{1,70}apply today'
    r'|(?:please )?(?:click here|apply now)\b|all qualified applicants\b|(?:this|the) (?:role|position) does not require regular travel'
    r'|[\w’\' .&-]+ commitment to (?:growth|inclusion|diversity)\b|to better equip our stores\b|environmental factors vary\b'
    r'|for positions in this location, we offer|[\w’\' .&-]+ offers a comprehensive benefits package\b'
    r'|range and benefit information|[\w’\' .&-]+ maintains broad salary ranges|position level and salary will be commensurate'
    r'|[\w’\' .&-]+ provides a competitive compensation package|an online assessment is part of the application process'
    r'|visa sponsorship\s*:\s*we do sponsor visas\b|years of experience required will correlate\b)', re.I,
)
BOILERPLATE = re.compile(
    r'\b(?:equal opportunity employer|without regard to|protected veteran status'
    r'|paid (?:time off|parental leave|holidays)|401\s*\(?\s*k\)?|employee discount|tuition assistance'
    r'|dental(?:,)? (?:and )?vision (?:coverage|insurance)|comprehensive benefits package|privacy (?:notice|policy)'
    r'|health insurance, flexible|federal, state, & local laws|is not contingent upon program award'
    r'|we (?:seek|aim) to build an inclusive|training and development opportunities)\b', re.I,
)
RESPONSIBILITY = re.compile(
    r'^(?:you(?:[’\']ll| will) (?:lead|manage|own|build|develop|design|support|deliver|perform)'
    r'|responsible for|report(?:s|ing) to|(?:lead|manage|own|develop|execute|build|design|support|deliver|perform'
    r'|coordinate|implement|oversee|partner|ensure|drive|maintain|collaborate|provide|assist)\s)', re.I,
)
PREFERRED_LINE = re.compile(
    r'\b(?:preferred|desired|strong plus|a plus|advantageous|nice[- ]to[- ]have|a bonus|helpful but not required)'
    r'(?:[.);!\s]*$|\s+but not required\b)|^(?:preferred|desired|optional)\s*:'
    r'|\bpreferred[;,]\s*(?:or\s+)?equivalent\b', re.I,
)
REQUIRED_LINE = re.compile(
    r'^(?:required|mandatory|minimum)\s*:|\b(?:is|are) (?:required|mandatory)\b|'
    r'^must (?:have|hold|possess|be|demonstrate|meet)\b|\b(?:license|certification|degree) required\b'
    r'|(?<!as )(?<!if )\brequired[. ]*$|\bmust be eligible to obtain\b', re.I,
)
EXPLICIT_OUTSIDE = re.compile(
    r'\b(?:degree|\d+\+? years?|certification|credential|license|licensure)\b.*\brequired[. ]*$'
    r'|\bmust be eligible to obtain\b'
    r'|^(?:(?:field )?experience\b|able and willing to work\b|strong .{1,50}\bskills?\b).+\b(?:required|preferred)[. ]*$', re.I,
)

TYPE_RULES = {
    'education': r'\b(?:degree|diploma|bachelor|master|doctorate|ph\.?d|high school|ged|mba|b\.?s|m\.?s|gpa|majors? accepted|enrolled|accredited law school)\b',
    'experience': r'\b(?:(?:\d+\+?|one|two|three|four|five|six|seven|eight|nine|ten)(?:\s+or more)?\s*(?:years?|months?)|relevant experience|(?:equivalent (?:work |professional )?|professional |work )experience)\b',
    'certification': r'\b(?:certification|certified|credential|pmp|cpa|cfa|acls|bls|cissp|six sigma belt)\b',
    'license': r'\b(?:licen[cs](?:e|ed|ure)|driver[’\']?s license|professional registration|series (?:7|63)|registered nurse)\b',
    'specialized_experience': r'\b(?:experience (?:with|in|working|supporting|managing|developing|performing|leading|using|operating|of)|background in|industry experience|specializ(?:ed|ation))\b',
    'technical_competency': r'\b(?:technical (?:skills|competenc\w*)|proficien\w*|proficiencies|excel|sql|python|java(?:script)?|sap|aws|azure|hris|rest apis?|kubernetes|microsoft office|cad|network protocols|software|programming|analytics|linux|salesforce|servicenow|skilled in)\b',
    'work_eligibility': r'\b(?:work authorization|authorized to work|security clearance|eligible to work|visa sponsorship|without sponsorship|u\.?s\.? citizenship|export control compliance)\b',
    'physical': r'\b(?:lift(?:ing)? (?:up to )?\d+|stand(?:ing)? for|physical (?:ability|requirements?))\b',
}
TYPE_RULES = {kind: re.compile(pattern, re.I) for kind, pattern in TYPE_RULES.items()}
QUALIFICATION_CUE = re.compile(
    r'\b(?:experience|knowledge|skills?|ability to|familiarity|proficien\w*|'
    r'competenc\w*|understanding|track record|demonstrated|expertise|background in|certificat\w*|'
    r'licen[cs]\w*|degree|diploma|eligible|fluency|fluent|bilingual|willingness|work flexible hours'
    r'|exposure to|analytical mindset|attention to detail|comfortable (?:with|managing)|collaborative and persuasive'
    r'|intellectual curiosity|clear communicator|strong writer|self-starter|professional in human resources|data analysis'
    r'|flexible (?:with scheduling|work schedule)|punctual attendance|written and verbal communication'
    r'|have (?:independently |successfully )?(?:led|built|delivered|turned)|you[’\']ve (?:designed|directed|been))\b', re.I,
)
ALTERNATIVE_START = re.compile(r'^(?:or\s+|in lieu of\b|alternatively\b|an equivalent combination\b)', re.I)
ALTERNATIVE_END = re.compile(r'(?:\bor|\band/or)\s*$', re.I)
LIST_INTRO = re.compile(r'\b(?:proficien\w*|experience|knowledge|skills|expertise|familiarity)\b[^:]{0,100}:$', re.I)
EMPTY = re.compile(r'^(?:none(?: required)?|n/?a|not (?:specified|applicable)|no (?:minimum|preferred) qualifications)(?:[. ]*)$', re.I)
SECTION_PLACEHOLDER = re.compile(r'^outlined below are the (?:optional preferred|required minimum) qualifications', re.I)
SUBHEADING = re.compile(r'(?:education (?:&|and) experience|skills\s*/\s*specialized knowledge\s*/\s*competencies|licenses?\s*/\s*training)', re.I)
QUALIFICATION_LABEL = re.compile(r'(?:minimum education|required field of study|minimum years of experience)', re.I)


def heading_parts(line):
    # Only the comparison form is normalized. Stored evidence retains the source
    # words, capitalization and punctuation.
    heading, separator, tail = re.split(r'([:：])', line, maxsplit=1) if re.search(r'[:：]', line) else (line, '', '')
    key = normalize('NFKC', heading.translate(FORMAT_MARKS)).strip().rstrip(' .…–—-')
    if separator and QUALIFICATION_LABEL.fullmatch(key):
        if not tail.strip() or FOOTER.search(tail.strip()):
            return 'stop', None, ''
        return 'required', heading.strip(), line
    if SUBHEADING.fullmatch(key) and not tail.strip():
        return 'subheading', heading.strip(), ''
    for kind, pattern in (
        ('preferred', PREFERRED_HEADING), ('required', REQUIRED_HEADING), ('ambiguous', AMBIGUOUS_HEADING),
    ):
        if pattern.fullmatch(key):
            return kind, heading.strip(), tail.strip() if separator else ''
    if re.match(r'^physical requirements may (?:include|involve)\b', line, re.I):
        return None, None, line
    if BOUNDARY.search(key) or FOOTER.search(line):
        return 'stop', None, ''
    return None, None, line


def statement_blocks(blocks, default_kind):
    kind, heading = default_kind, None
    pending = None
    lead_in = None
    for number, (raw, path) in enumerate(blocks, start=1):
        statement = LIST_ITEM.sub('', raw).translate(FORMAT_MARKS).strip()
        if SECTION_PLACEHOLDER.match(statement):
            continue
        next_kind, next_heading, text = heading_parts(statement)
        if next_kind:
            if pending:
                yield pending
                pending = None
            if next_kind == 'subheading':
                lead_in = None
            else:
                kind, heading, lead_in = next_kind, next_heading, None
        if not text:
            continue
        if LIST_INTRO.search(text) and kind:
            if pending:
                yield pending
                pending = None
            lead_in = (text, path)
            continue
        if lead_in:
            _, parent = lead_in
            if path is not None and parent is not None and (len(path) <= len(parent) or path[:len(parent)] != parent):
                lead_in = None
            elif path is None and QUALIFICATION_CUE.search(text):
                lead_in = None
        if pending:
            previous, prev_kind, prev_heading, prev_number, has_lead = pending
            if ALTERNATIVE_START.match(text) or ALTERNATIVE_END.search(previous):
                pending = (f'{previous} {text}', prev_kind, prev_heading, prev_number, has_lead)
                continue
            yield pending
        pending = (f'{lead_in[0]} {text}' if lead_in else text, kind, heading, number, bool(lead_in))
    if pending:
        yield pending


def classify_statement(text, kind, inherited_list, field, types):
    if EMPTY.fullmatch(text) or BOILERPLATE.search(text):
        return None
    if kind == 'stop' and not EXPLICIT_OUTSIDE.search(text):
        return None
    preferred = bool(PREFERRED_LINE.search(text))
    required = bool(REQUIRED_LINE.search(text)) and not re.search(r'\bnot required\b', text, re.I)
    if field == 'educationRequirements' and 'education' not in types:
        return None
    if field == 'experienceRequirements' and not {'experience', 'specialized_experience'}.intersection(types):
        return None
    if RESPONSIBILITY.match(text) and not (required or preferred or 'license' in types or 'certification' in types):
        return None
    if preferred and required:
        return 'ambiguous'
    if preferred:
        return 'preferred'
    if required:
        return 'required'
    if kind in KINDS and (field in DEDICATED_FIELDS and DEDICATED_FIELDS[field] != 'ambiguous'
                         or inherited_list or QUALIFICATION_CUE.search(text) or types):
        return kind
    return None


def extract_qualifications(source, source_url, *, limit_per_kind=24):
    """Read every supplied block and then enforce independent output budgets.

    The input must already be authorized and verified by its caller. Evidence
    contains source wording with whitespace and bullet layout normalized.
    A missing field means no evidence was extracted from the supplied source.
    """
    url = urlsplit(source_url)
    if url.scheme != 'https' or not url.hostname or url.username or url.password:
        raise ValueError('Expected a verified HTTPS employer posting URL')
    if limit_per_kind is not None and (type(limit_per_kind) is not int or limit_per_kind < 0):
        raise ValueError('Expected a nonnegative integer output limit or None for audit')

    selected = {}
    conflicts = set()
    fields = [(field, kind) for field, kind in DEDICATED_FIELDS.items() if field in source]
    fields.extend((('description', None), ('responsibilities', 'stop'), ('ExternalResponsibilitiesStr', 'stop')))
    for field, default_kind in fields:
        for text, section_kind, heading, number, inherited_list in statement_blocks(
                positioned_blocks(source.get(field)), default_kind):
            dedicated = field != 'description'
            types = tuple(label for label, pattern in TYPE_RULES.items() if pattern.search(text))
            kind = classify_statement(text, section_kind, inherited_list, field, types)
            if not kind:
                continue
            evidence = Evidence(text, kind, types, source_url, field, heading, number,
                                'medium' if kind == 'ambiguous' else 'high')
            key = text.casefold().rstrip('.;')
            prior = selected.get(key)
            if key in conflicts:
                continue
            if not prior or prior.kind == 'ambiguous' and kind != 'ambiguous':
                selected[key] = evidence
            elif prior.kind != kind and kind != 'ambiguous':
                if prior.source_field != 'description' and not dedicated:
                    continue
                conflicts.add(key)
                selected[key] = Evidence(prior.text, 'ambiguous', prior.types, prior.source_url,
                                         prior.source_field, prior.section, prior.block, 'medium')

    kept = []
    counts = dict.fromkeys(KINDS, 0)
    omitted = dict.fromkeys(KINDS, 0)
    for evidence in selected.values():
        if limit_per_kind is not None and counts[evidence.kind] >= limit_per_kind:
            omitted[evidence.kind] += 1
        else:
            kept.append(evidence)
            counts[evidence.kind] += 1
    return Extraction(tuple(kept), omitted)
