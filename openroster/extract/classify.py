"""Keyword rules for type, roles, mode, eligibility, cost and CS relevance. Deterministic and explainable."""

from __future__ import annotations

import re

# Order matters: the first matching rule wins.
TYPE_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("hackathon", re.compile(r"\bhack\b|\bhack(?:athon|s\b|ing\b|fest|\s?day|\s?night)|\b\w+hacks\b|\bdatathon|\bideathon|\bbuildathon|\bcode\s?jam|\bgame\s?jam", re.I)),
    ("case_competition", re.compile(r"\bcase (?:comp(?:etition)?|challenge)|\bpitch (?:competition|comp)\b|\bstock pitch", re.I)),
    ("career_fair", re.compile(r"\b(?:career|job|co-?op|internship|tech) (?:fair|expo)\b|\brecruit(?:ment|ing) fair", re.I)),
    ("info_session", re.compile(r"\binfo(?:rmation)?\s?session|\binfo night|\bopen house|\bon[- ]campus (?:visit|tour)|\bcoffee chat|\bmeet (?:the|our) (?:team|recruiters)|\bdiscover \w+\b|\bcompany (?:visit|presentation)", re.I)),
    ("conference", re.compile(r"\bconference\b|\bsummit\b|\bsymposium\b|\bcon\s?20\d\d\b|\btech week\b", re.I)),
    ("workshop", re.compile(r"\bworkshop|\bbootcamp|\bhands[- ]on\b|\bstudy jam|\bcrash course|\btutorial\b|\bresume (?:review|clinic)|\binterview prep", re.I)),
    ("tech_talk", re.compile(r"\btech talk|\bspeaker series|\bseminar\b|\bcolloquium|\blecture\b|\bfireside|\bpanel\b|\bkeynote|\bdistinguished", re.I)),
    ("networking", re.compile(r"\bnetworking|\bmixer\b|\bmeet(?:up| and greet)|\bsocial\b|\bgathering\b|\bmingle", re.I)),
    ("early_career_program", re.compile(r"\bfellowship|\bexternship|\binsight (?:program|day|week)|\bfirst[- ]year program|\bsecond[- ]year program|\bdiscovery (?:program|day)|\bambassador program|\bstudent program|\bscholars? program|\bleadership program|\bmentorship program", re.I)),
]

ROLE_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("volunteer", re.compile(r"\bvolunteer", re.I)),
    ("mentor", re.compile(r"\bmentor(?:s|ing)?\b(?! program)", re.I)),
    ("judge", re.compile(r"\bjudg(?:e|es|ing)\b", re.I)),
    ("organizer_team", re.compile(r"\b(?:join (?:our|the) (?:organizing )?team|organi[sz]er (?:application|recruitment)|we(?:'re| are) hiring organi[sz]ers|exec(?:utive)? (?:team )?(?:application|recruitment))", re.I)),
    ("workshop_lead", re.compile(r"\b(?:workshop (?:lead|host|facilitator|proposal)s?|run a workshop|host a workshop|call for (?:speakers|workshops|proposals))", re.I)),
]

# Relevance for campus-wide calendars (sources with `filter: cs`). Strong terms count anywhere, including the
# description. Broad terms ("tech", "data", "app", "career") show up in the descriptions of almost any campus event
# ("download the app", "data collection"), so they count only in the title, host or categories.
CS_STRONG = re.compile(
    r"\b(?:hackathons?|hack ?(?:nights?|days?)|\w*hacks\b|coding|programming|programmers?|software|developers?|computer science|"
    r"comp ?sci|computing|machine learning|artificial intelligence|deep learning|data science|cyber ?security|"
    r"robotics|fintech|quantitative|devops|github|python|javascript|java\b|blockchain|game dev(?:elopment)?|"
    r"tech talks?|career fairs?|job fairs?|women in (?:tech|stem|computing)|in tech\b|ctf\b|capture the flag)",
    re.I,
)
# Campus admin and teaching-staff items that mention tech words but are not opportunities for students.
NOT_OPPORTUNITY = re.compile(
    r"\b(?:for tas?\b|teaching assistants?|faculty fellows?|brightspace|academic integrity|last day to|"
    r"registration (?:opens|closes|deadline)|deadline to (?:drop|add|withdraw)|senate|board of governors|"
    r"convocation|exam (?:period|schedule)|reading week|tuition)",
    re.I,
)
CS_FOCUS = re.compile(
    r"\b(?:hack(?:s|ing)?|tech|technology|technical|\bai\b|\bml\b|\bcs\b|data|analytics|engineer(?:s|ing)?|startups?|"
    r"entrepreneur(?:s|ship)?|innovation|digital|web|apps?\b|ux|ui\b|cloud|cyber|product management|"
    r"google|microsoft|amazon|aws|azure|ibm|shopify|quant|stem\b|co-?op|internships?|recruit(?:ing|ment)?|"
    r"resumes?|cv\b|interviews?|job search|linkedin|careers?|networking|pitch|incubator|accelerator)",
    re.I,
)

ONLINE = re.compile(r"\b(?:virtual|online|zoom|teams meeting|webinar|livestream|remote|google meet)\b", re.I)
IN_PERSON = re.compile(r"\b(?:in[- ]person|on[- ]campus|in[- ]office|room\b|hall\b|building|campus|auditorium|venue)\b", re.I)
HYBRID = re.compile(r"\bhybrid\b", re.I)

HIGH_SCHOOL = re.compile(r"\bhigh[- ]school(?:ers)?\b|\bsecondary school|\bgrades? (?:9|10|11|12)\b", re.I)
GRAD = re.compile(r"\b(?:graduate students?|grad students?|master'?s|phd|doctoral|postdoc)\b", re.I)
UNDERGRAD = re.compile(r"\b(?:undergrad(?:uate)?s?|first[- ]year|second[- ]year|third[- ]year|1st[- ]year|2nd[- ]year|post-?secondary)\b", re.I)
SCHOOL_ONLY = re.compile(r"\b(?:students? only|current students|open to [A-Z][a-z]+ students|student (?:id|card) required|must be (?:a|an) [A-Z]\w+ student)", re.I)
OPEN_TO_ALL = re.compile(r"\b(?:open to (?:all|everyone|the public|students from any)|all (?:students|schools) welcome|everyone is welcome)\b", re.I)

FREE = re.compile(r"\b(?:free(?: of charge| admission| to attend| event)?|no cost|no charge|complimentary)\b", re.I)
PAID = re.compile(r"(?:\$\s?\d+|\bCAD\s?\d+|\bticket(?:s)? (?:cost|price)|\bregistration fee|\badmission:? \$)", re.I)
TRAVEL = re.compile(r"\b(?:travel (?:reimbursement|grants?|support|stipend|subsid)|bus(?:es)? (?:from|provided)|reimburse(?:ment)? for travel)", re.I)


def classify_type(text: str, default: str | None = None) -> str | None:
    for name, rx in TYPE_RULES:
        if rx.search(text):
            return name
    return default


def detect_roles(text: str) -> list[str]:
    return [name for name, rx in ROLE_RULES if rx.search(text)]


def detect_mode(text: str) -> str:
    if HYBRID.search(text):
        return "hybrid"
    online, in_person = bool(ONLINE.search(text)), bool(IN_PERSON.search(text))
    if online and in_person:
        return "hybrid"
    if online:
        return "online"
    if in_person:
        return "in_person"
    return "unknown"


def detect_eligibility(text: str) -> list[str]:
    out: list[str] = []
    if OPEN_TO_ALL.search(text):
        out.append("open_to_all")
    if SCHOOL_ONLY.search(text):
        out.append("school_only")
    if HIGH_SCHOOL.search(text):
        out.append("high_school")
    if UNDERGRAD.search(text):
        out.append("undergrad")
    if GRAD.search(text):
        out.append("grad")
    return out or ["unknown"]


def detect_cost(text: str) -> str:
    if PAID.search(text):
        return "paid"
    if FREE.search(text):
        return "free"
    return "unknown"


def mentions_travel_support(text: str) -> bool:
    return bool(TRAVEL.search(text))


def is_cs_relevant(text: str, title: str | None = None) -> bool:
    """`text` is everything known about the item; `title` is its title plus host and categories, when the
    adapter can tell them apart. Without a title, only the strong terms count."""
    if title and NOT_OPPORTUNITY.search(title):
        return False
    if CS_STRONG.search(text):
        return True
    return bool(title and (CS_STRONG.search(title) or CS_FOCUS.search(title)))


# Who an opportunity is aimed at. Tags only: they power the "Who it's for" filter and never hide anything.
AUDIENCE_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("first_year", re.compile(r"\b(?:first[- ]year|1st[- ]year|freshm(?:an|en)|year 1 students|first and second[- ]year|1st/2nd)\b", re.I)),
    ("second_year", re.compile(r"\b(?:second[- ]year|2nd[- ]year|sophomores?|first and second[- ]year|1st/2nd)\b", re.I)),
    ("women_nonbinary", re.compile(r"\b(?:women|woman|female|non-?binary|gender[- ]diverse|gender[- ]expansive|she\+|herhacks|ellehacks|wit\b|women in (?:tech|stem|computing))", re.I)),
    ("black_students", re.compile(r"\b(?:black (?:students|engineers|in tech|professionals)|afro|nsbe)\b", re.I)),
    ("indigenous_students", re.compile(r"\b(?:indigenous|first nations|m[eé]tis|inuit)\b", re.I)),
    ("lgbtq", re.compile(r"\b(?:lgbtq\+?|2slgbtqia\+?|queer|pride)\b", re.I)),
    ("beginner_friendly", re.compile(r"\b(?:beginners?(?:[- ]friendly)?|no experience (?:needed|required)|first[- ]time hackers?|newcomers? welcome)\b", re.I)),
]


def detect_audience(text: str) -> list[str]:
    return [tag for tag, rx in AUDIENCE_RULES if rx.search(text)]
