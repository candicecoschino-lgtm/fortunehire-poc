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
    'header', 'li', 'ol', 'p', 'section', 'table', 'td', 'th', 'tr', 'ul',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
}
HIDDEN_TAGS = {'script', 'style', 'template', 'noscript'}
HEADING_TAGS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
LIST_ITEM = re.compile(r'^\s*(?:[•●▪◦‣·*]|[-–—](?=\s)|\d+[.)](?=\s))\s*')
SPACE = re.compile(r'\s+')
FORMAT_MARKS = str.maketrans('', '', '\u200b\u200c\u200d\ufeff\u200e\u200f')
LABELED_LIST_CRITERION = re.compile(
    r'^(?:[\w/&+#-]+\s+){0,5}[\w/&+#-]+:\s+'
    r'(?:(?:hands-on|proven|demonstrated)\s+)?(?:experience|proficiency|knowledge|skills)\b', re.I,
)


class DescriptionBlocks(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.blocks = []
        self.hidden = []
        self.list_depth = 0
        self.list_path = []
        self.next_list = 0
        self.in_heading = False
        self.list_line_break = False
        self.feed(html)
        self.close()
        self.flush()

    def flush(self):
        value = SPACE.sub(' ', ''.join(self.parts)).strip()
        if value:
            self.blocks.append((value, tuple(self.list_path), self.in_heading))
        self.parts.clear()
        self.list_line_break = False

    def handle_starttag(self, tag, attrs):
        if tag in HIDDEN_TAGS:
            self.hidden.append(tag)
        if self.hidden:
            return
        if tag in HEADING_TAGS:
            self.flush()
            self.in_heading = True
        elif tag in ('ul', 'ol'):
            self.flush()
            self.next_list += 1
            self.list_path.append(self.next_list)
        elif tag == 'li':
            self.flush()
            self.list_depth += 1
        elif tag in BLOCK_TAGS and not self.list_depth:
            self.flush()
        elif tag == 'br' or self.list_depth and tag in BLOCK_TAGS:
            if tag == 'br':
                self.list_line_break = True
            self.parts.append(' ')

    def handle_endtag(self, tag):
        if self.hidden:
            if self.hidden[-1] == tag:
                self.hidden.pop()
            return
        if tag in HEADING_TAGS:
            self.flush()
            self.in_heading = False
        elif tag in ('ul', 'ol'):
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
            if self.list_line_break and data.strip():
                if LABELED_LIST_CRITERION.match(data.strip()):
                    self.flush()
                self.list_line_break = False
            self.parts.append(data)


HTML_TAG = re.compile(r'</?(?:h[1-6]|p|div|li|ul|ol|br|strong|b|span|section|script|style|table)\b', re.I)


def description_blocks(value):
    if not isinstance(value, str):
        return []
    html = value if HTML_TAG.search(value) else unescape(value)
    if HTML_TAG.search(html):
        return DescriptionBlocks(html).blocks
    return [(line.strip(), None, False) for line in html.splitlines() if line.strip()]


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
    return (text for text, _, _ in positioned_blocks(value))


QUAL = (
    r'(?:qualifications?(?:, capabilities,? and skills)?|requirements?|(?:technical )?skills?'
    r'(?:\s*(?:and|&|/)\s*(?:experience|abilities))?|education(?:\s+and\s+experience)?'
    r'|(?:years of (?:\w+ )?|leadership )?experience|licen[cs](?:e|ure)s?|certifications?|credentials?|clearances?)'
)
REQUIRED_HEADING = re.compile(
    rf'(?:(?:(?:additional|job|role|position) )?(?:required|minimum|basic|mandatory|essential|critical)(?: required)? {QUAL}'
    r'|(?:job|position|minimum) requirements?(?: we seek)?|minimum qualifications and requirements'
    r'|minimum education/experience requirements?|required field of study|your skills (?:and|&) abilities \(required qualifications\)'
    r'|what(?:[’\']s| is) needed to succeed \(minimum qualifications\)'
    r'|(?:basic|minimum|required) (?:qualifications?|requirements?) \(required skills\s*(?:/| and )\s*experience\)'
    r'|what you(?:[’\']ll| will) need(?: to have)?|what you need to succeed'
    r'|experience and educational requirements?|skills and experience required'
    r'|minimum skills,\s*knowledge,?\s*and ability requirements'
    r'|what you(?:[’\']ll| will) bring\s*[-–—:]\s*required'
    r'|you(?:[’\']ll| will) (?:have|need)(?: (?:the following|to have))?|required|requirements)', re.I,
)
PREFERRED_HEADING = re.compile(
    rf'(?:(?:additional )?(?:preferred|desired|desirable|optional) {QUAL}|preferred(?: qualifications?)?'
    r'|nice[- ]to[- ]have(?:s)?|desired|optional|bonus points|what sets you apart|desired characteristics(?: and eligibility| & eligibility)?'
    r'|(?:additional |other )?(?:preferred|desired|optional) (?:technical |professional )?(?:background|experience|competencies|criteria|credentials|certifications|education|attributes|knowledge|skills)(?: (?:and|&) (?:experience|skills|qualifications))?'
    r'|what we (?:prefer|would like)|what (?:else|we) (?:would love|love) to see|bonus if you have'
    r'|even better(?:,)? (?:if you have|you may have)(?: one or more of the following)?'
    r'|what makes you stand out(?:\s*[-–—:]\s*preferred)?|it[’\']d be great if you (?:also )?have'
    r'|preferred certifications include one or more of'
    r'|preferred skills\s*/\s*certifications?|preferred qualifications \(desired skills\s*(?:/| and )\s*experience\)'
    r'|what will give you a competitive edge \(preferred (?:qualifications|skills)\)'
    r'|your skills (?:and|&) abilities \(preferred qualifications\))', re.I,
)
AMBIGUOUS_HEADING = re.compile(
    rf'(?:{QUAL}|qualifications\s*(?:/|and)\s*(?:requirements|skills)|requirements and qualifications'
    r'|(?:additional|other) (?:job |eligibility )?requirements?'
    r'|education(?: and |\s*/\s*)experience(?: requirements?)?|your skills (?:and|&) abilities \(qualifications\)'
    r'|physical requirements|work authorization|security clearance|export control requirements|visa sponsorship'
    r'|you might thrive in this role if you|what makes you a great fit|ideal candidate profile|skills and competencies'
    r'|(?:relevant )?work experience|certifications? \(if applicable\)'
    r'|about you|who you are|(?:who|what) we(?:[’\']re| are) looking for|what we expect'
    r'|important skills|soft skills|skills and knowledge|skills (?:&|and) capabilities'
    r'|competencies|licen[cs]es?\s*/\s*certifications?|training and travel requirements?'
    r'|education and work experience|candidate experience'
    r'|to be successful in this role,? you have'
    r'|what you(?:(?:[’\']ll| will) bring| bring))', re.I,
)
BOUNDARY = re.compile(
    r'^(?:(?:about (?:us|the company|the team|the role|the job|[A-Z][\w -]+)|who we are|company (?:overview|description)'
    r'|(?:key |primary |essential |position |job |role )*(?:responsibilities|duties|accountabilities)'
    r'|(?:the )?role overview|job (?:description|summary)|position summary|work environment|working conditions'
    r'|(?:physical|travel|location|worksite) requirements|compensation(?: (?:and benefits|range|details))?|pay(?: transparency| range| details)?'
    r'|(?:annual )?salary(?: range)?|benefits(?: and perks)?|total rewards|what (?:we|[\w .&-]+) offers?|why (?:join|work)|how to apply|after you apply'
    r'|equal (?:employment|opportunity)|accommodations?|legal (?:notice|disclaimer)|additional information'
    r'|schedule|shift|relocation(?: assistance)?|employment type|job category|application (?:deadline|process)'
    r'|drug[- ]free workplace|(?:primary|job) location|disclaimer|logistics|what success looks like'
    r'|perks and benefits|employees at all levels are expected to|other duties|work location|direct manager|to be considered'
    r'|(?:location-based |office )?hybrid policy)\b'
    r'|what you(?:[’\']ll| will) (?:do|be doing|work on)\b|where you(?:[’\']ll| will) be working\b)', re.I,
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
    r'|visa sponsorship\s*:\s*we do sponsor visas\b|years of experience required will correlate\b'
    r'|individual pay is determined\b|this position has a base salary range\b|the annual compensation range\b'
    r'|for sales roles, the range provided\b|at [\w .&-]+, we connect people to the care they need\b'
    r'|(?:if .*?, )?we encourage you to apply\b|please (?:submit|complete) (?:an?|the|your) application\b'
    r'|from fortune\. |at [\w .&-]+, we[’\']re revolutionizing\b'
    r'|discounts up to \d+%|you build connection\. you show up\b)', re.I,
)
EQUAL_OPPORTUNITY = re.compile(r'\bis an equal opportunity (?:employer|workplace)\b', re.I)
BOILERPLATE = re.compile(
    r'\b(?:equal opportunity employer|without regard to|protected veteran status'
    r'|paid (?:time off|parental leave|holidays)|401\s*\(?\s*k\)?|employee discount|tuition assistance'
    r'|dental(?:,)? (?:and )?vision (?:coverage|insurance)|comprehensive benefits package|privacy (?:notice|policy)'
    r'|health insurance, flexible|federal, state, & local laws|is not contingent upon program award'
    r'|we (?:seek|aim) to build an inclusive|training and development opportunities'
    r'|paid time away|vacation time off program|eligible to earn annual bonuses|encouraged to apply'
    r'|is a drug\s*[-–]\s*free workplace'
    r'|i acknowledge that the position for which i am applying)\b', re.I,
)
RESPONSIBILITY = re.compile(
    r'^(?:you(?:[’\']ll| will) (?:lead|manage|own|build|develop|design|support|deliver|perform)'
    r'|responsible for|report(?:s|ing) to|(?:lead|manage|own|develop|execute|build|design|support|deliver|perform'
    r'|coordinate|implement|oversee|partner|ensure|drive|maintains?|collaborate|provides?|assists?|performs?|participate)\s)', re.I,
)
PREFERRED_LINE = re.compile(
    r'\b(?:preferred|desired|strong plus|a plus|advantageous|nice[- ]to[- ]have|a bonus|helpful(?: but not required)?)'
    r'(?:[.);!\s]*$|,?\s+but not required\b)'
    r'|^(?:[\w ]+:\s+)?(?:(?:highly )?preferred|desired|optional)(?:\s*:|\s+(?:\d|an?\b|fluency\b|experience\b))'
    r'|\bpreferred[;,.]\s*(?:or\s+)?equivalent\b|^while\b[^,]+\bis preferred,', re.I,
)
INLINE_PREFERENCE = re.compile(
    r'\(preferred\)(?=\s*(?:[,.;]|$))|\bpreferred\s+\((?:i\.e\.|e\.g\.)'
    r'|\b(?:degree|credential|certification|experience) preferred in\b', re.I,
)
PREFERENCE_SUFFIX = re.compile(
    r',\s+(with\b[^.!?]*\bpreferred[.!?]?|'
    r'(?:ideally|preferably)\s+(?:within|in|with|from)\b[^.!?]+[.!?]?)$', re.I,
)
PREFERENCE_MODIFIER = re.compile(r'^(?:ideally|preferably)\b', re.I)
COORDINATED_PREFERENCE = re.compile(r',\s+and\s+([^.!?]+\b(?:is|are)\s+(?:(?:highly|strongly)\s+)?preferred[.!?]?)$', re.I)
KEY_DETAILS = re.compile(r'^key details\s*:\s*', re.I)
POSSIBLE_REQUIREMENT = re.compile(r'\bmay be required\s+(?:by|for|in|when|if|depending on)\b', re.I)
REQUIRED_CLAUSE = re.compile(r'(?<!not )(?<!strictly )\brequired\s*[,;.]', re.I)
REQUIRED_LINE = re.compile(
    r'^(?:required|mandatory|minimum)\s*:|^required\s+(?:\d|an?\b)|\b(?:is|are) (?:required|mandatory)\b|'
    r'^must (?:have|hold|possess|be|demonstrate|meet|maintain|obtain|secure|carry|retain)\b|\b(?:license|certification|degree|licensure) required\b'
    r'|^requires? (?:completion|graduation|graduate|\d+|broad training|(?:[\w-]+ ){0,3}skills|'
    r'(?:an? )?(?:(?:bachelor|master)[’\']s |doctoral )?(?:degree|diploma|certification|licen[cs]\w*))\b'
    r'|^(?:this )?(?:position|role) requires (?:at least|a minimum of)\b'
    r'|\brequired, (?:demonstrated|including|unless|subject to)\b'
    r'|(?<!as )(?<!if )(?<!when )(?<!where )\brequired[. ]*$|\bmust be eligible to obtain\b', re.I,
)
LICENSE_OBLIGATION = re.compile(
    r'^(?:(?:candidates? |you )?must (?:have|hold|possess|maintain|(?:be willing to )?obtain|secure|carry|retain)|maintains?|requires?) '
    r'(?:(?!records?\b|documentation\b|lists?\b)(?:[\w’\'-]+|\([\w -]+\)) ){0,7}'
    r'(?:licen[cs]\w*|certif\w*|credentials?|clearance)\b'
    r'|^(?:(?:candidates?|you) )?must be willing to obtain\b[^.!?]{0,100}'
    r'\b(?:licen[cs]e|licensure|certification|credential)\b', re.I,
)
EXPLICIT_CREDENTIAL = re.compile(
    r'^(?:an? )?(?:active|current|valid|unrestricted)\b'
    r'[^.!?]*\b(?:degree|licen[cs]\w*|certif\w*|credentials?|clearance)\b[^.!?]*\brequired\b'
    r'|\bmust be eligible to obtain\b', re.I,
)
DUTY_SECTION_EVIDENCE = re.compile(
    r'^(?:(?:field )?experience\b|able and willing to work\b|strong .{1,50}\bskills?\b|'
    r'(?:(?:\d+\+?|at least \d+) years?|bachelors?|masters?|doctorate|high school diploma)\b)'
    r'.+\b(?:required|preferred)[. ]*$', re.I,
)
CONDITIONAL_ELIGIBILITY = re.compile(
    r'^(?:candidates(?: for .{1,90}? positions)? must be (?:a [\w.]+ citizen|legally authorized|eligible to work)'
    r'|this position is subject to [^.]+ qualification requirements for\b'
    r'|(?:export control license\s*:\s*)?this (?:position|role) may require a deemed export control license\b'
    r'.*\bplacement is contingent\b)', re.I,
)
CANDIDATE_AGE = re.compile(r'^candidates? must be (?:at least \d+ years? old|\d+ years? or older)\b', re.I)
SUMMARY_REQUIREMENT = re.compile(
    r'^(?:you must be comfortable\b|to be successful,? you need to be\b'
    r'|(?:in addition, )?you must possess\b.{0,100}\b(?:skills?|expertise|experience)\b'
    r'|this (?:role|position) requires\b.{0,100}\b(?:skills?|expertise|experience)\b'
    r'|(?:excellent|strong) .{1,180}\bskills?\b.*\b(?:is|are) (?:also )?required[.!?]?$'
    r'|the desire and ability to .+\bis essential[.!?]?$)', re.I,
)
JOB_LOGISTICS = re.compile(
    r'^(?:key details\s*:\s*)?(?:(?:ability (?:and willingness )?to|willingness to|candidates? must be able to) '
    r'(?:travel\b|commute\b|(?:temporarily )?work at (?:alternative|alternate|other) sites?\b'
    r'|provide coverage at other (?:sites|locations)\b'
    r'|work in an environment that operates 24\s*/\s*7\b|participate in shift rotations\b)'
    r'|(?:domestic and/or international |domestic |international )?travel up to \d+%'
    r'|travel(?:ing|ling)? within\b|you will be required to work shift work\b'
    r'|(?:overnight|frequent|occasional) travel\b|experience with extensive travel\b'
    r'|will be responsible to cover emergency service calls\b'
    r'|this is a (?:fully )?remote position(?=\s*(?:[.!?]|$|with a work schedule\b))'
    r'|this position is (?:fully )?(?:remote|on-?site|hybrid)(?: with \d+% travel required)?(?=\s*[.!?]?\s*$)'
    r'|(?:(?:the )?(?:typical |regular )?(?:work )?schedule is|hours are|'
    r'this position works (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|'
    r'(?:candidates? )?must (?:reside (?:in|within)|be willing to relocate)|'
    r'strong preference will be given to candidates who reside in|'
    r'field-based travel|dedicated remote workspace|'
    r'ability to work the designated schedule|flexibility to adjust start/finish times|'
    r'comfortable with physical requirements)\b'
    r'|willing/able to (?:adhere to the schedule|work (?:at least [\w-]+ )?(?:evenings|weekends|holidays))\b'
    r'|all (?:employees working remotely|telecommuters) will be required to adhere to\b[^.!?]*\btelecommut\w* polic(?:y|ies)\b'
    r'|(?:access to a designated quiet workspace|live in a location that can receive|'
    r'(?:live|reside) within (?:a reasonable commuting|a commutable) distance)\b'
    r'|(?:ability to|must be able to) lift (?:up to )?[\w-]+(?: [\w-]+)? (?:lbs|pounds)\b'
    r'|can (?:carry/lift|lift) (?:up to )?\d+ (?:lbs|pounds)\b'
    r'|(?:adequate|sufficient) mobility (?:to|for)\b'
    r'|ability to perform physical tasks required for\b'
    r'|available to work (?:an? )?(?:weekend|holiday) rotation\b'
    r'|remote from [^.,;]+[.!?]?$'
    r'|(?:must be available for (?:an? )?on[- ]call (?:rotation|coverage)'
    r'|on[- ]call (?:rotation|coverage) (?:is )?required)\b'
    r'|ability to train as [\w -]+ and adhere to standards\b'
    r'|all physical requirements are expected with reasonable accommodations\b'
    r'|willingness and demonstrated ability to work in the following physical conditions\b)', re.I,
)
DRIVER_LICENSE = r'(?:an? )?(?:valid |current )?driver[’\']?s license'
RELIABLE_TRANSPORTATION = r'(?:access to )?(?:a )?(?:reliable (?:means of )?|(?:their |your )?own )transportation'
TRAVEL_AND_TRANSPORTATION = re.compile(
    r'^(?:key details\s*:\s*)?(?:(?:(?:proven )?ability(?:/willing| and willingness)? to|'
    r'willingness(?: and ability)? to|(?:candidates? |you )?must(?: be (?:able|willing) to)?|'
    r'(?:be )?able to|willing/able to|requires?) )?'
    r'(?:(?:(?:domestic(?: and(?:/or)? international)?|international|overnight|frequent|occasional|local|field) )*travel\b'
    r'(?=\s*(?:[.!?,;:(]|$)|\s+up to(?=\s*\d)|\s+(?:to|within|across|throughout|up to|as needed|when required|approximately|'
    r'as required|locally|domestically|internationally|extensively|required|may|is|will|in|between|every)\b'
    r'|\s+(?:\d+\s*%|and (?:work overtime|(?:may )?require (?:overnight|local|field) travel)\b))'
    r'|up to\s*\d+\s*%\s+(?:local |overnight |field )?travel\b'
    r'|travel(?:ing|ling) within\b|field-based travel\b|experience with extensive travel\b'
    r'|(?:this|the) (?:remote )?(?:position|role) requires (?:up to\s*\d+\s*%\s+)?'
    r'(?:(?:local|frequent|overnight|field) )*travel(?=\s*(?:[.!?]|$)|\s+(?:for|to|within|of|up to)\b)'
    r'|this position is (?:fully )?(?:remote|on-?site|hybrid) with \d+% travel required\b'
    r'|this is a field[- ]based position\s*[-–:]\s*(?:up to )?\d+\s*%\s+travel\b'
    r'|(?:ability to |willingness to |must be able to )commute\b'
    r'|you will be responsible for having a reliable personal vehicle and '
    rf'{DRIVER_LICENSE} to travel\b'
    r'|(?:(?:you )?must (?:have|possess) |possess )?(?:'
    rf'{DRIVER_LICENSE}(?: and |,\s*){RELIABLE_TRANSPORTATION}'
    r'(?:,?\s+and (?:required )?(?:automobile|vehicle|liability) insurance)?'
    rf'|{RELIABLE_TRANSPORTATION}(?: and {DRIVER_LICENSE})?'
    rf'|{DRIVER_LICENSE} and vehicle insurance,\s*(?:access to )?a (?:dependable|reliable) vehicle,?\s+or public transportation'
    r'|access to a (?:dependable|reliable)(?: personal)? vehicle'
    r')\b(?=\s*[.!?:]?$))', re.I,
)
AMBIGUOUS_WORK_CONTEXT = re.compile(
    r'^(?:(?:able to|must be able to|willing/able to|ability to|willingness to) work\b[^.!?]*\bovertime\b'
    r'|work overtime\b|\(?overtime (?:is |may be )?(?:required|mandatory)\b'
    r'|flexibility to adjust start/finish times\b[^.!?]*\bovertime\b)', re.I,
)
LOGISTICS_CLAUSE_BOUNDARY = re.compile(r',?\s+and\s+|;\s+', re.I)
SENTENCE_BOUNDARY = re.compile(
    r'(?<=[.!?])(?<!\b[A-Za-z]\.)\s+(?=[A-Z]|\d+\s*\+?\s*(?:years?|months?)\b)'
    r'|(?<=[aApP]\.[mM]\.)\s+(?=[A-Z][a-z])|(?<=;)\s+(?=(?i:normally requires?)\b)',
)
INLINE_APPLICATION_DEADLINE = re.compile(r'^application deadline\s*[:：]\s*\S', re.I)
DUTY_LEAD = re.compile(r'\bwhile you\s*:$', re.I)
TENURE_NUMBER = r'(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)'
SHARED_SKILL_TENURE = (
    rf'(?:must have|requires?) (?:at least )?{TENURE_NUMBER}\s+(?:years?|months?) of '
    r'(?:[\w-]+ ){0,5}experience in the following skills?(?:\(s\))?\s*:'
)
SHARED_SKILL_HEADING = re.compile(SHARED_SKILL_TENURE, re.I)
INLINE_SKILL_TENURE = re.compile(rf'(?<=[.!?])\s+(?={SHARED_SKILL_TENURE})', re.I)
NUMBERED_SKILL = re.compile(r'^\s*(?:\(\d+\)|\d+[.)])\s+')
REFERENCE_SUFFIX = re.compile(r'(?<=[.!?])\s*#\d{4}$')
TENURE_FLOOR = re.compile(
    rf'^(?:you (?:have|bring) )?(?:a minimum of |minimum(?: of)? |at least ){TENURE_NUMBER}\s*'
    r'\+?\s*(?:years?|months?)\b', re.I,
)

TYPE_RULES = {
    'education': r'\b(?:degree|diploma|bachelor|master|doctorate|ph\.?d|high school|ged|mba|b\.?a|b\.?s|m\.?s|gpa|majors? accepted|enrolled|accredited law school|(?:graduate|rn) from (?:an? )?accredited)\b',
    'experience': r'\b(?:(?:\d+\+?|one|two|three|four|five|six|seven|eight|nine|ten)(?:\s+or more)?\s*(?:years?|months?)|relevant experience|(?:equivalent (?:work |professional )?|professional |work )experience)\b',
    'certification': r'\b(?:certification|certified|credential|pmp|cpa|cfa|acls|bls|cissp|six sigma belt)\b',
    'license': r'\b(?:licen[cs](?:e|ed|ure)|driver[’\']?s license|professional registration|series (?:7|63)|registered nurse)\b',
    'specialized_experience': r'\b(?:experience (?:with|in|working|supporting|managing|developing|performing|leading|using|operating|of)|background in|industry experience|specializ(?:ed|ation))\b',
    'technical_competency': r'\b(?:technical (?:skills|competenc\w*)|proficien\w*|proficiencies|excel|sql|python|java(?:script)?|sap|aws|azure|hris|rest apis?|kubernetes|terraform|microsoft office|cad|network protocols|software|programming|analytics|linux|salesforce|servicenow|skilled in)\b',
    'work_eligibility': r'\b(?:work authorization|authorized to work|legally permitted to work|security clearance|eligible to work|visa sponsorship|without sponsorship|u\.?s\.? citizen(?:ship)?|export control compliance)\b',
    'physical': r'\b(?:lift(?:ing)? (?:up to )?\d+|stand(?:ing)? for|physical (?:ability|requirements?))\b',
}
TYPE_RULES = {kind: re.compile(pattern, re.I) for kind, pattern in TYPE_RULES.items()}
QUALIFICATION_CUE = re.compile(
    r'\b(?:experience|knowledge|skills?|ability to|familiarity|proficien\w*|'
    r'competenc\w*|understanding|track record|demonstrated|expertise|background in|certificat\w*|'
    r'licen[cs]\w*|degree|diploma|eligible|fluency|fluent(?:ly)?|bilingual|willingness|work flexible hours'
    r'|exposure to|analytical mindset|attention to detail|comfort(?:able)? (?:with|managing|working|building)|collaborative and persuasive'
    r'|proven (?:record|success|ability)|skilled at|openness to|passion for|experienced in'
    r'|financial acumen|functional specifications|collaborative mindset|tech-savvy mindset|commitment to continuous learning'
    r'|self-directed|existing network|strong account planning|employment visa|work authorization assistance'
    r'|you[’\']ve built|mechanical inclination'
    r'|intellectual curiosity|clear communicator|strong writer|self-starter|professional in human resources|data analysis'
    r'|available online portfolio'
    r'|flexible (?:with scheduling|work schedule)|punctual attendance|written and verbal communication'
    r'|have (?:independently |successfully )?(?:led|built|delivered|turned)|you[’\']ve (?:designed|directed|been))\b', re.I,
)
ALTERNATIVE_START = re.compile(r'^(?:or\s+|in lieu of\b|alternatively\b|an equivalent combination\b)', re.I)
ALTERNATIVE_END = re.compile(r'(?:\bor|\band/or)\s*$', re.I)
LIST_INTRO = re.compile(r'\b(?:proficien\w*|experience|knowledge|skills|expertise|familiarity)\b[^:]{0,100}:$', re.I)
EMPTY = re.compile(
    r'^(?:none(?: required)?|n/?a|not (?:specified|applicable|required)|[-–—*]+'
    r'|no (?:minimum |preferred |additional |previous )?(?:qualifications?|education|'
    r'certifications?|(?:years? of )?(?:\w+ )?experience))(?:[. ]*)$', re.I,
)
SECTION_PLACEHOLDER = re.compile(r'^outlined below are the (?:optional preferred|required minimum) qualifications', re.I)
SUBHEADING = re.compile(
    r'(?:education (?:&|and) experience|skills\s*/\s*specialized knowledge\s*/\s*competencies'
    r'|licenses?\s*/\s*training|experience\s*(?:&|and)\s*skills|personal attributes|specific skills)', re.I,
)
TENURE_LABEL = re.compile(r'(?:(?:minimum|preferred) )?years of (?:\w+ )?experience|relevant work experience', re.I)
BARE_TENURE = re.compile(r'\d+(?:\s*[-–+]\s*\d*)?(?:\s+(?:years?|months?))?\.?', re.I)
CHOICE_INTRO = re.compile(r'\b(?:one of|one or more of|any of) the following\b[^:]*:$', re.I)
PREFERRED_CHOICE = re.compile(
    r'(?:one|one or more|any) of the following(?: \w+)? (?:is|are) (?:preferred|desired|optional)[.:]?', re.I,
)
SUPPLEMENT = re.compile(r'^(?:as (?:business needs|applicable law) dictate|where required by law|subject to \w)', re.I)
DUTY_HEADING = re.compile(r'\b(?:responsibilities|duties|accountabilities)\b|^what you(?:[’\']ll| will) (?:do|be doing|work on)', re.I)
MIXED_CREDENTIALS = re.compile(
    r'((?:[\w./]+ )*(?:degree|diploma|certification|credential|MBA|BA/BS|BS|BA) required)'
    r'[,;]\s+((?:[\w./]+ )+preferred[.!]?)', re.I,
)
MIXED_SIGNALS = re.compile(r'\b(?:preferred|preferably|ideally|nice[- ]to[- ]have|bonus|not required)\b', re.I)
FLOOR_SECTION = re.compile(
    r'qualifications?(?: and skills)?|(?:work )?experience|education and work experience|to be successful in this role,? you have'
    r'|what you(?:[’\']ll| will) bring', re.I,
)
APPLICATION_SUFFIX = re.compile(
    r'(?<=[.!?])\s+(?:new graduates are encouraged to apply|please (?:apply|submit) your application)\.?$', re.I,
)
ELIGIBILITY_DISCLOSURE = re.compile(
    r'(?<=[.!?])\s+(?=any information (?:obtained|collected) during (?:the )?registration\b)', re.I,
)
RUN_ON_HEADING = re.compile(r'(?i:^((?:minimum|preferred|required|basic) qualifications?))(?=[A-Z][a-z])')
INLINE_PAY = re.compile(r'(?<=[.!?])\s*(?=(?:pay|salary|compensation) range\s*:)|(?<=preferred)(?=Pay Range\s*:)', re.I)
INLINE_VALUE_LABEL = re.compile(
    r'(?:minimum education|required field of study|education\s*/\s*experience|candidate experience'
    r'|licen[cs]es?\s*/\s*certifications?)', re.I,
)
PROCESS_SUFFIX = re.compile(r'(?<=[.!?])\s+for further information,? please consult\b[^.!?]*[.!?]?$', re.I)
CONTINUATION_STUB = re.compile(r'\b(?:an?|the) (?:national|accredited|recognized)\s*$', re.I)
NORMALLY_REQUIRED = re.compile(r'^normally requires?\b', re.I)
INLINE_ALTERNATIVE = re.compile(r'^required\s+(?=or\s+equivalent\b)', re.I)
CONDITION_CONTINUATION = re.compile(r'^(?:if|when|where|unless|except|provided that)\b', re.I)
CHOICE_SENTENCE = re.compile(r'\b(?:one|one or more|any) of the following(?:\s+\w+)?\s+(?:is|are)\b', re.I)
SHIFT_HEADING = re.compile(r'(?:shift(?: details)?|schedule)', re.I)
DRIVING_RECORD_HEADING = re.compile(r'(?:required\s*\(driving record\)|driving record requirements?)', re.I)
NO_PRIOR_EXPERIENCE = re.compile(r'^no (?:prior )?(?:[\w-]+ ){0,4}experience (?:is )?(?:needed|required|necessary)[.!]?$', re.I)
GENERIC_CREDENTIAL_DUTY = re.compile(r'^maintain all required (?:certifications? and licenses?|licenses? and certifications?) as required\b', re.I)
ACCREDITED_PROGRAM = re.compile(r'^(?:graduate|rn) from (?:an? )?accredited\b', re.I)
DEGREE_PATH = re.compile(r'^(?:an? )?(?:bachelor|master|doctoral|associate)\b', re.I)
HIGH_SCHOOL_DIPLOMA = (
    r'(?:a )?high school diploma(?:\s*(?:/|,|or)\s*'
    r'(?:ged|general education (?:development|degree)(?:\s*\(ged\))?))?'
)
HIGH_SCHOOL_ONLY = re.compile(rf'(?:requires? completion of )?{HIGH_SCHOOL_DIPLOMA}(?: is)?(?: required)?[.]?', re.I)
HIGH_SCHOOL_ALTERNATIVE = re.compile(
    rf'{HIGH_SCHOOL_DIPLOMA} or equivalent (?:work |professional )?experience(?: is)? required[.]?', re.I,
)
SKILL_CONTEXT_REQUIREMENT = re.compile(
    r'\b(?:recognize|determine|understand|know)\s+(?:when|where|if)\b[^.!?]{0,60}\b(?:is|are) required\b', re.I,
)


def heading_parts(line):
    # Normalize the heading for comparison while preserving the source wording.
    if FOOTER.search(line) or EQUAL_OPPORTUNITY.search(line):
        return 'stop', None, ''
    if DUTY_LEAD.search(line):
        return 'duties', None, ''
    parts = re.split(r'[:：]|(?<=\s)[–—-](?=\s)', line, maxsplit=1)
    candidates = [(line, '')]
    run_on = RUN_ON_HEADING.match(line)
    if run_on:
        candidates.append((run_on[1], line[run_on.end():]))
    if len(parts) == 2:
        candidates.append((parts[0], parts[1].strip()))
    for heading, tail in candidates:
        label = heading.strip().rstrip(' .…–—-:：')
        key = normalize('NFKC', label)
        if SHIFT_HEADING.fullmatch(key):
            # A shift header can precede an unlabeled qualifications list.
            return 'logistics', label, ''
        if DRIVING_RECORD_HEADING.fullmatch(key):
            return 'stop', label, ''
        if SUBHEADING.fullmatch(key) and not tail:
            return 'subheading', label, ''
        if TENURE_LABEL.fullmatch(key):
            label_kind = 'ambiguous'
            if key.lower().startswith('minimum'):
                label_kind = 'required'
            elif key.lower().startswith('preferred'):
                label_kind = 'preferred'
            return label_kind, label, tail
        for kind, pattern in (
            ('preferred', PREFERRED_HEADING), ('required', REQUIRED_HEADING), ('ambiguous', AMBIGUOUS_HEADING),
        ):
            if pattern.fullmatch(key):
                if tail and INLINE_VALUE_LABEL.fullmatch(key):
                    tail = line
                return kind, label, tail
    if re.match(r'^physical requirements may (?:include|involve)\b', line, re.I):
        return None, None, line
    if BOUNDARY.search(line):
        return 'duties' if DUTY_HEADING.search(parts[0]) else 'stop', None, ''
    return None, None, line


def grouped_skill_blocks(blocks):
    """Keep a shared tenure threshold attached to its entire skills list."""
    group = None
    child_list = None
    for number, (raw, path, is_heading) in enumerate(blocks, start=1):
        if group:
            first, lead, parent, members = group
            nested = False
            if path is not None and parent is not None and len(path) > len(parent) and path[:len(parent)] == parent:
                root = path[:len(parent) + 1]
                if child_list is None:
                    child_list = root
                nested = root == child_list
            text_bullet = path == parent and (LIST_ITEM.match(raw) or NUMBERED_SKILL.match(raw))
            if not is_heading and (nested or text_bullet):
                members.append(raw.strip())
                continue
            yield first, ' '.join([lead, *members]), parent, False
            group = None
            child_list = None
        intro = LIST_ITEM.sub('', SPACE.sub(' ', raw)).strip()
        if not is_heading and SHARED_SKILL_HEADING.fullmatch(intro):
            group = (number, intro, path, [])
        else:
            yield number, raw, path, is_heading
    if group:
        first, lead, parent, members = group
        yield first, ' '.join([lead, *members]), parent, False


def statement_blocks(blocks, default_kind):
    kind, heading = default_kind, None
    pending = None
    previous_path = None
    lead_in = None
    scoped_sections = []
    logistics_path = None
    for number, raw, path, is_heading in grouped_skill_blocks(blocks):
        if logistics_path:
            if path and len(path) > len(logistics_path) and path[:len(logistics_path)] == logistics_path:
                continue
            logistics_path = None
        while scoped_sections:
            section_path, parent_kind, parent_heading = scoped_sections[-1]
            if path and path[:len(section_path)] == section_path:
                break
            if pending:
                yield pending
                pending = None
            scoped_sections.pop()
            kind, heading, lead_in = parent_kind, parent_heading, None
        statement = SPACE.sub(' ', LIST_ITEM.sub('', raw).translate(FORMAT_MARKS)).strip()
        statement = APPLICATION_SUFFIX.sub('', statement)
        statement = PROCESS_SUFFIX.sub('', statement)
        statement = INLINE_PAY.split(statement, maxsplit=1)[0]
        if CONDITIONAL_ELIGIBILITY.match(statement):
            statement = ELIGIBILITY_DISCLOSURE.split(statement, maxsplit=1)[0]
        if not statement or SECTION_PLACEHOLDER.match(statement):
            continue
        if path and statement.endswith(':') and (TRAVEL_AND_TRANSPORTATION.match(statement)
                                                  or JOB_LOGISTICS.match(statement)
                                                  or AMBIGUOUS_WORK_CONTEXT.match(statement)):
            logistics_path = path
        if kind is None and INLINE_APPLICATION_DEADLINE.match(statement):
            continue
        next_kind, next_heading, text = heading_parts(statement)
        if is_heading and next_kind is None:
            next_kind, text = 'stop', ''
        if next_kind:
            if pending:
                yield pending
                pending = None
            if next_kind == 'subheading':
                lead_in = None
                if kind not in KINDS and re.fullmatch(r'education (?:and|&) experience', next_heading, re.I):
                    kind, heading = 'ambiguous', next_heading
            else:
                if path and (not scoped_sections or scoped_sections[-1][0] != path):
                    scoped_sections.append((path, kind, heading))
                kind, heading, lead_in = next_kind, next_heading, None
        if not text:
            continue
        if heading and TENURE_LABEL.fullmatch(heading) and BARE_TENURE.fullmatch(text):
            if not re.fullmatch(r'0(?: years?)?\.?', text):
                rendered = text if kind == 'ambiguous' else f'{heading}: {text}'
                yield (rendered, kind, heading, number, True)
            kind, heading, lead_in = default_kind, None, None
            continue
        preferred_choice = PREFERRED_CHOICE.fullmatch(text)
        choice = preferred_choice or CHOICE_INTRO.search(text)
        if kind in KINDS and (LIST_INTRO.search(text) or choice):
            if pending:
                yield pending
                pending = None
            lead_in = (text, path, bool(choice), 'preferred' if preferred_choice else kind)
            continue
        if lead_in:
            _, parent, choice, _ = lead_in
            if path is not None and parent is not None and (len(path) <= len(parent) or path[:len(parent)] != parent):
                lead_in = None
            elif path is None and (choice or QUALIFICATION_CUE.search(text)):
                lead_in = None
        if pending:
            previous, prev_kind, prev_heading, prev_number, has_lead = pending
            same_list = path == previous_path
            explicit_continuation = (ALTERNATIVE_START.match(text) or ALTERNATIVE_END.search(previous)
                                     or SUPPLEMENT.match(text)
                                     or INLINE_ALTERNATIVE.match(text) and REQUIRED_LINE.search(previous))
            unfinished_phrase = text[0].islower() and CONTINUATION_STUB.search(previous)
            grouped_choice = lead_in and lead_in[2]
            if (grouped_choice and lead_in[3] == 'preferred' and same_list and not explicit_continuation
                    and explicit_preference(text)):
                lead_in = None
                grouped_choice = False
            if same_list and (explicit_continuation or unfinished_phrase or grouped_choice):
                pending = (f'{previous} {text}', prev_kind, prev_heading, prev_number, has_lead)
                continue
            yield pending
        scoped_list = bool(path or LIST_ITEM.match(raw)) and (
            kind in ('required', 'preferred') or heading and heading.casefold() == 'competencies')
        pending = (f'{lead_in[0]} {text}' if lead_in else text, lead_in[3] if lead_in else kind,
                   heading, number, bool(lead_in or scoped_list))
        previous_path = path
    if pending:
        yield pending


def split_travel_clause(sentence):
    starts_with_travel = TRAVEL_AND_TRANSPORTATION.match(sentence)
    for boundary in LOGISTICS_CLAUSE_BOUNDARY.finditer(sentence):
        before = sentence[:boundary.start()]
        after = sentence[boundary.end():]
        if (not starts_with_travel and TRAVEL_AND_TRANSPORTATION.match(after)
                and (QUALIFICATION_CUE.search(before) or AMBIGUOUS_WORK_CONTEXT.match(before))):
            return before, after
        if TRAVEL_AND_TRANSPORTATION.match(before) and (
                explicit_requirement(after) or explicit_preference(after) or AMBIGUOUS_WORK_CONTEXT.match(after)):
            return before, after
    return (sentence,)


def separate_work_context(text):
    """Keep overtime as context and discard travel and transportation logistics."""
    parts = []
    for sentence in SENTENCE_BOUNDARY.split(text):
        for clause in split_travel_clause(sentence):
            context = AMBIGUOUS_WORK_CONTEXT.match(clause)
            travel = TRAVEL_AND_TRANSPORTATION.match(clause)
            if travel or context or JOB_LOGISTICS.match(clause) or NO_PRIOR_EXPERIENCE.match(clause):
                if parts:
                    yield ' '.join(parts), False
                    parts.clear()
                if context and not travel:
                    yield clause, True
            else:
                parts.append(clause)
    if parts:
        yield ' '.join(parts), False


def summary_requirements(text, *, include_explicit=False):
    sentences = SENTENCE_BOUNDARY.split(text)
    for i, sentence in enumerate(sentences):
        sentence = KEY_DETAILS.sub('', sentence)
        coordinated = COORDINATED_PREFERENCE.search(sentence) if include_explicit else None
        if coordinated:
            sentence = sentence[:coordinated.start()]
        kind = 'required' if SUMMARY_REQUIREMENT.match(sentence) else None
        if kind or (include_explicit and has_strength_cue(sentence)
                    and not TYPE_RULES['work_eligibility'].search(sentence)):
            following = sentences[i + 1:i + 2]
            if following and (ALTERNATIVE_START.match(following[0]) or SUPPLEMENT.match(following[0])):
                sentence = f'{sentence} {following[0]}'
            yield from split_preference(sentence, kind)
        if coordinated:
            yield coordinated[1], 'preferred'


def strength_content(text):
    label, separator, tail = text.partition(':')
    return tail.strip() if separator and INLINE_VALUE_LABEL.fullmatch(label.strip()) else text


def explicit_requirement(text):
    content = strength_content(text)
    direct = POSSIBLE_REQUIREMENT.sub('', SKILL_CONTEXT_REQUIREMENT.sub('', content))
    return bool(REQUIRED_LINE.search(direct) or LICENSE_OBLIGATION.search(direct) or EXPLICIT_CREDENTIAL.search(direct))


def explicit_preference(text):
    content = strength_content(text)
    return bool(PREFERRED_LINE.search(content) or INLINE_PREFERENCE.search(content))


def has_strength_cue(text):
    return bool(explicit_requirement(text) or explicit_preference(text) or NORMALLY_REQUIRED.match(text)
                or POSSIBLE_REQUIREMENT.search(text))


def independent_criteria(text, kind):
    """Separate independently labeled sentences and retain explanatory continuations."""
    parts = []
    for sentence in SENTENCE_BOUNDARY.split(text):
        if parts and not (CHOICE_SENTENCE.search(parts[0]) or CONDITION_CONTINUATION.match(sentence)):
            labeled = has_strength_cue(parts[0]) and has_strength_cue(sentence)
            education = kind == 'required' and ACCREDITED_PROGRAM.match(parts[0]) and DEGREE_PATH.match(sentence)
            if labeled or education:
                yield ' '.join(parts)
                parts.clear()
        parts.append(sentence)
    yield ' '.join(parts)


def split_preference(text, kind):
    preference = PREFERENCE_SUFFIX.search(text)
    if preference and (explicit_requirement(text[:preference.start()])
                       or kind == 'required' and PREFERENCE_MODIFIER.match(preference[1])):
        yield text[:preference.start()], kind
        yield preference[1], 'preferred'
    else:
        yield text, kind


def qualification_statements(blocks, default_kind):
    for raw, kind, heading, number, inherited_list in statement_blocks(blocks, default_kind):
        key_details = kind is None and bool(KEY_DETAILS.match(raw))
        for text, work_context in separate_work_context(REFERENCE_SUFFIX.sub('', raw)):
            if work_context:
                if kind != 'stop':
                    yield text, 'work_context', heading, number, inherited_list
                continue
            if kind in (None, 'duties'):
                include_explicit = key_details or (kind is None and explicit_preference(text)
                                                   and SENTENCE_BOUNDARY.search(text))
                explicit = list(summary_requirements(text, include_explicit=include_explicit))
                if explicit or key_details:
                    for criterion, strength in explicit:
                        yield criterion, strength, heading, number, True
                    continue
            if kind in KINDS:
                criteria = INLINE_SKILL_TENURE.split(text, maxsplit=1)
                if len(criteria) == 2 and TYPE_RULES['education'].search(criteria[0]):
                    for criterion in criteria:
                        yield criterion, kind, heading, number, inherited_list
                    continue
            mixed = MIXED_CREDENTIALS.fullmatch(text) if kind not in ('stop', 'duties', 'preferred') else None
            if mixed:
                yield mixed[1], 'required', heading, number, inherited_list
                yield mixed[2], 'preferred', heading, number, inherited_list
            else:
                criteria = independent_criteria(text, kind) if kind not in ('stop', 'duties') else (text,)
                for criterion in criteria:
                    for fragment, strength in split_preference(criterion, kind):
                        yield fragment, strength, heading, number, inherited_list or strength != kind


def has_scoped_tenure_floor(text, heading):
    return bool(heading and FLOOR_SECTION.fullmatch(heading) and TENURE_FLOOR.match(text)
                and ('experience' in text.lower() or heading.casefold().endswith('experience'))
                and not MIXED_SIGNALS.search(text))


def classify_statement(text, kind, heading, inherited_list, field, types):
    if kind == 'work_context':
        return 'ambiguous'
    if (EMPTY.fullmatch(text) or BOILERPLATE.search(text) or FOOTER.search(text)
            or TRAVEL_AND_TRANSPORTATION.match(text) or JOB_LOGISTICS.match(text)
            or GENERIC_CREDENTIAL_DUTY.match(text)):
        return None
    license_obligation = bool(LICENSE_OBLIGATION.search(text))
    credential_required = bool(EXPLICIT_CREDENTIAL.search(text))
    conditional_eligibility = bool(CONDITIONAL_ELIGIBILITY.search(text))
    candidate_age = bool(CANDIDATE_AGE.match(text))
    if kind == 'stop' and not conditional_eligibility:
        return None
    if kind == 'duties' and not (license_obligation or credential_required or conditional_eligibility or candidate_age
                                 or DUTY_SECTION_EVIDENCE.match(text)):
        return None
    content = strength_content(text)
    if kind == 'logistics' and not ((types or QUALIFICATION_CUE.search(content))
                                    and (explicit_requirement(content) or explicit_preference(content))):
        return None
    preferred = explicit_preference(content)
    required = explicit_requirement(content) or conditional_eligibility or candidate_age
    if NORMALLY_REQUIRED.match(content) or (POSSIBLE_REQUIREMENT.search(content) and not required):
        return 'ambiguous'
    if heading and re.fullmatch(r'education\s*/\s*experience', heading, re.I):
        required |= bool(re.search(r'\brequires \d+\b', content, re.I))
    if re.search(r'\bnot (?:strictly )?required\b', text, re.I):
        required = False
        if not preferred and kind == 'required':
            return 'ambiguous'
    if field == 'educationRequirements' and 'education' not in types:
        return None
    if field == 'experienceRequirements' and not {'experience', 'specialized_experience'}.intersection(types):
        return None
    if RESPONSIBILITY.match(text) and not (license_obligation or credential_required or preferred):
        return None
    if preferred and (required or REQUIRED_CLAUSE.search(text)):
        return 'ambiguous'
    if preferred or kind == 'preferred':
        if preferred or required or inherited_list or QUALIFICATION_CUE.search(text) or types or field in DEDICATED_FIELDS:
            return 'preferred'
        return None
    if required:
        return 'required'
    if kind == 'ambiguous' and has_scoped_tenure_floor(text, heading):
        return 'required'
    if kind == 'ambiguous' and heading and heading.casefold() == 'skills' and ';' in text:
        return 'ambiguous'
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
    fields.extend((('description', None), ('responsibilities', 'duties'), ('ExternalResponsibilitiesStr', 'duties')))
    for field, default_kind in fields:
        for text, section_kind, heading, number, inherited_list in qualification_statements(
                positioned_blocks(source.get(field)), default_kind):
            types = tuple(label for label, pattern in TYPE_RULES.items() if pattern.search(text))
            kind = classify_statement(text, section_kind, heading, inherited_list, field, types)
            if not kind:
                continue
            if default_kind == 'preferred' and kind == 'required':
                kind = 'ambiguous'
            confidence = 'medium' if kind == 'ambiguous' or (
                kind == 'required' and section_kind == 'ambiguous' and has_scoped_tenure_floor(text, heading)
            ) else 'high'
            evidence = Evidence(text, kind, types, source_url, field, heading, number,
                                confidence)
            key = text.casefold().rstrip('.;')
            prior = selected.get(key)
            if key in conflicts:
                continue
            if not prior or prior.kind == 'ambiguous' and kind != 'ambiguous':
                selected[key] = evidence
            elif prior.kind != kind and kind != 'ambiguous':
                conflicts.add(key)
                selected[key] = Evidence(prior.text, 'ambiguous', prior.types, prior.source_url,
                                         prior.source_field, prior.section, prior.block, 'medium')

    education_alternatives = {(item.source_field, item.block) for item in selected.values()
                              if item.kind == 'required' and HIGH_SCHOOL_ALTERNATIVE.fullmatch(item.text)}
    kept = []
    counts = dict.fromkeys(KINDS, 0)
    omitted = dict.fromkeys(KINDS, 0)
    for evidence in selected.values():
        # Adjacent restatements of the same credential must preserve the accepted equivalent.
        if evidence.kind == 'required' and HIGH_SCHOOL_ONLY.fullmatch(evidence.text) and any(
                (evidence.source_field, evidence.block + gap) in education_alternatives for gap in (1, 2)):
            continue
        if limit_per_kind is not None and counts[evidence.kind] >= limit_per_kind:
            omitted[evidence.kind] += 1
        else:
            kept.append(evidence)
            counts[evidence.kind] += 1
    return Extraction(tuple(kept), omitted)
