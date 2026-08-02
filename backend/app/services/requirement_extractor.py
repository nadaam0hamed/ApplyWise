"""Extract structured scholarship requirements from retrieved knowledge-base text.

Uses regex pattern matching only — no LLM inference — so values are never hallucinated.
Extracts normalized ``StructuredRequirement`` payloads alongside legacy display strings.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from langchain_core.documents import Document

from app.schemas.requirement_matching import RetrievedRequirement, StructuredRequirement

_WORD_NUMBERS: dict[str, int] = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}

_WORD_NUMBER_PATTERN = "|".join(_WORD_NUMBERS)

_DEGREE_ALIASES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"bachelor|undergraduate", re.IGNORECASE), "Bachelor"),
    (re.compile(r"master(?:'?s)?(?!\s+of\s+business)", re.IGNORECASE), "Master"),
    (re.compile(r"mba|master\s+of\s+business", re.IGNORECASE), "MBA"),
    (re.compile(r"doctoral|doctorate|ph\.?\s*d", re.IGNORECASE), "Doctoral"),
    (re.compile(r"associate", re.IGNORECASE), "Associate"),
)

_DOCUMENT_KEYWORDS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bpassport\b", re.IGNORECASE), "passport"),
    (re.compile(r"\b(?:academic\s+)?transcript\b", re.IGNORECASE), "academic_transcript"),
    (re.compile(r"\b(?:CV|curriculum\s+vitae|resume)\b", re.IGNORECASE), "cv"),
    (re.compile(r"\bstatement\s+of\s+purpose\b", re.IGNORECASE), "statement_of_purpose"),
    (re.compile(r"\b(?:motivation\s+letter|letter\s+of\s+motivation)\b", re.IGNORECASE), "motivation_letter"),
    (re.compile(r"\brecommendation\s+letters?\b", re.IGNORECASE), "recommendation_letters"),
    (re.compile(r"\b(?:degree|diploma|graduation)\s+certificate\b", re.IGNORECASE), "graduation_certificate"),
    (re.compile(r"\bresearch\s+proposal\b", re.IGNORECASE), "research_proposal"),
    (re.compile(r"\b(?:financial|bank)\s+(?:documents?|statements?)\b", re.IGNORECASE), "financial_documents"),
    (re.compile(r"\bvisa\b", re.IGNORECASE), "visa"),
)


def _compile(patterns: tuple[str, ...]) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(p, re.IGNORECASE) for p in patterns)


def _parse_count(raw: str) -> int | None:
    cleaned = raw.strip().lower()
    if cleaned.isdigit():
        return int(cleaned)
    return _WORD_NUMBERS.get(cleaned)


def _normalize_degree(raw: str) -> str:
    for pattern, label in _DEGREE_ALIASES:
        if pattern.search(raw):
            return label
    return raw.strip().title()


def _normalize_country(raw: str) -> str:
    cleaned = raw.strip()
    cleaned = re.sub(
        r"\s+(?:only|are\s+eligible|is\s+eligible|may\s+apply|can\s+apply|will\s+be\s+considered).*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s+(?:and|or)\s+.*$", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip(" .,;")


def _normalize_country_list(raw: str) -> list[str]:
    parts = re.split(r",|\band\b|\bor\b|;", raw, flags=re.IGNORECASE)
    countries = [_normalize_country(part) for part in parts if part.strip()]
    return [country for country in countries if country]


def _normalize_major(raw: str) -> str:
    cleaned = raw.strip(" .,;:")
    cleaned = re.sub(
        r"\s+(?:is\s+)?(?:required|preferred|expected|mandatory).*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()


def _normalize_deadline(raw: str) -> str:
    return re.sub(r"\s+", " ", raw.strip(" .,;:"))


def _build_structured(
    req_type: str,
    *,
    operator: str | None = None,
    value: Any = None,
) -> StructuredRequirement:
    return StructuredRequirement(type=req_type, operator=operator, value=value)


@dataclass(frozen=True)
class _PatternSpec:
    field: str
    req_type: str
    patterns: tuple[re.Pattern[str], ...]
    formatter: str
    operator: str | None = None
    is_boolean: bool = False
    value_from_group: Callable[[re.Match[str]], Any] | None = None


def _numeric_from_group(group_index: int = 1) -> Callable[[re.Match[str]], float | int | None]:
    def _extract(match: re.Match[str]) -> float | int | None:
        raw = match.group(group_index)
        if raw is None:
            return None
        parsed = _parse_count(raw) if not re.search(r"\.", raw) else None
        if parsed is not None:
            return parsed
        try:
            return float(raw.replace(",", "."))
        except ValueError:
            return None

    return _extract


def _count_from_group(group_index: int = 1) -> Callable[[re.Match[str]], int | None]:
    def _extract(match: re.Match[str]) -> int | None:
        if match.lastindex is None or match.lastindex < group_index:
            return None
        raw = match.group(group_index)
        if raw is None:
            return None
        return _parse_count(raw)

    return _extract


def _text_from_group(group_index: int = 1, *, normalizer: Callable[[str], Any] | None = None) -> Callable[[re.Match[str]], Any]:
    def _extract(match: re.Match[str]) -> Any:
        raw = match.group(group_index)
        if raw is None:
            return None
        return normalizer(raw) if normalizer else raw.strip()

    return _extract


# --- Pattern specifications ---

_GPA_SPECS = _PatternSpec(
    field="gpa",
    req_type="gpa",
    patterns=_compile(
        (
            r"(?:applicants?\s+(?:must|should|are\s+expected\s+to)\s+(?:have|hold|maintain)\s+(?:a\s+)?)?"
            r"(?:minimum|min\.?|required)\s*(?:GPA|grade\s+point\s+average)\s*(?:of|:)?\s*(\d+\.?\d*)",
            r"(?:minimum|min\.?|required)\s*(?:GPA|grade\s+point\s+average)\s*(?:of|:)?\s*(\d+\.?\d*)",
            r"GPA\s*(?:of|at\s+least|minimum|≥|>=|:)\s*(\d+\.?\d*)",
            r"(\d+\.?\d*)\s*(?:/|\s*out\s+of\s*)\s*4\.?0?\s*(?:GPA|scale)?",
            r"cumulative\s+GPA\s*(?:of|:)?\s*(\d+\.?\d*)",
            r"(?:academic\s+background|eligibility)[^.]{0,80}?(?:minimum|min\.?)\s*GPA\s*(?:of|:)?\s*(\d+\.?\d*)",
            r"(?:candidates?|eligible\s+applicants?)\s+(?:must|should)\s+(?:have|maintain)\s+(?:a\s+)?GPA\s*(?:of|≥|>=|:)?\s*(\d+\.?\d*)",
        )
    ),
    formatter="Minimum GPA: {value}",
    operator=">=",
    value_from_group=_numeric_from_group(1),
)

_IELTS_SPECS = _PatternSpec(
    field="ielts",
    req_type="ielts",
    patterns=_compile(
        (
            r"(?:language\s+requirement|english\s+proficiency)[^.]{0,80}?"
            r"IELTS\s*(?:overall|minimum|min\.?|score)?\s*(?:of|:)?\s*(\d+\.?\d*)",
            r"IELTS\s*(?:overall|minimum|min\.?|score)?\s*(?:of|:)?\s*(\d+\.?\d*)",
            r"(?:minimum|min\.?|required)\s*(?:IELTS|band\s+score)\s*(?:of|:)?\s*(\d+\.?\d*)",
            r"overall\s*(?:IELTS\s*)?(?:band\s*)?(?:score\s*)?(?:of|:)?\s*(\d+\.?\d*)",
            r"IELTS\s+(?:academic\s+)?(?:minimum\s+)?(?:overall\s+)?(?:band\s+)?(\d+\.?\d*)",
            r"(?:applicants?\s+(?:must|should)\s+(?:achieve|obtain|have)\s+)?"
            r"(?:an?\s+)?IELTS\s+(?:score\s+of\s+)?(\d+\.?\d*)",
        )
    ),
    formatter="Minimum IELTS: {value}",
    operator=">=",
    value_from_group=_numeric_from_group(1),
)

_TOEFL_SPECS = _PatternSpec(
    field="toefl",
    req_type="toefl",
    patterns=_compile(
        (
            r"(?:language\s+requirement|english\s+proficiency)[^.]{0,80}?"
            r"TOEFL\s*(?:iBT|score)?\s*(?:of|:)?\s*(?:minimum|min\.?)?\s*(\d+)",
            r"TOEFL\s*(?:iBT|score)?\s*(?:of|:)?\s*(?:minimum|min\.?)?\s*(\d+)",
            r"(?:minimum|min\.?|required)\s*TOEFL\s*(?:iBT\s*)?(?:score\s*)?(?:of|:)?\s*(\d+)",
            r"(?:applicants?\s+(?:must|should)\s+(?:achieve|obtain|have)\s+)?"
            r"(?:an?\s+)?TOEFL\s+(?:iBT\s+)?(?:score\s+of\s+)?(\d+)",
        )
    ),
    formatter="Minimum TOEFL: {value}",
    operator=">=",
    value_from_group=_numeric_from_group(1),
)

_DUOLINGO_SPECS = _PatternSpec(
    field="duolingo",
    req_type="duolingo",
    patterns=_compile(
        (
            r"(?:language\s+requirement|english\s+proficiency)[^.]{0,80}?"
            r"Duolingo(?:\s+English\s+Test|\s+DET)?\s*(?:score)?\s*(?:of|:)?\s*(\d+)",
            r"Duolingo(?:\s+English\s+Test|\s+DET)?\s*(?:score)?\s*(?:of|:)?\s*(\d+)",
            r"(?:minimum|min\.?|required)\s*Duolingo\s*(?:English\s+Test\s*)?(?:score\s*)?(?:of|:)?\s*(\d+)",
            r"(?:minimum|min\.?|required)\s*DET\s*(?:score\s*)?(?:of|:)?\s*(\d+)",
        )
    ),
    formatter="Minimum Duolingo: {value}",
    operator=">=",
    value_from_group=_numeric_from_group(1),
)

_PASSPORT_SPECS = _PatternSpec(
    field="passport",
    req_type="passport",
    patterns=_compile(
        (
            r"(?:required\s+documents?[^.]{0,120}\b)?valid\s+passport",
            r"passport\s+(?:is\s+)?required",
            r"copy\s+of\s+(?:your\s+)?passport",
            r"passport\s+(?:must\s+be\s+)?valid",
            r"upload\s+(?:a\s+)?passport",
            r"applicants?\s+(?:must|should)\s+(?:submit|provide|upload)\s+(?:a\s+)?(?:copy\s+of\s+)?(?:their\s+)?passport",
        )
    ),
    formatter="Passport required",
    is_boolean=True,
)

_RECOMMENDATION_SPECS = _PatternSpec(
    field="recommendation_letters",
    req_type="recommendation_letters",
    patterns=_compile(
        (
            rf"(?:at\s+least\s+)?(\d+|{_WORD_NUMBER_PATTERN})\s*(?:letters?\s+of\s+)?recommendation",
            rf"recommendation\s+letters?\s*(?:\(|\:)?\s*(\d+|{_WORD_NUMBER_PATTERN})",
            rf"at\s+least\s+(\d+|{_WORD_NUMBER_PATTERN})\s*(?:letters?\s+of\s+)?recommendation",
            rf"(\d+|{_WORD_NUMBER_PATTERN})\s*(?:academic\s+)?(?:letters?\s+of\s+)?recommendation\s+(?:are\s+)?required",
            r"(?:required\s+documents?[^.]{0,120}\b)(?:at\s+least\s+)?(?:two|2|\d+)\s*(?:letters?\s+of\s+)?recommendation",
        )
    ),
    formatter="Recommendation letters required: {value}",
    operator=">=",
    value_from_group=_count_from_group(1),
)

_TRANSCRIPT_SPECS = _PatternSpec(
    field="transcript",
    req_type="academic_transcript",
    patterns=_compile(
        (
            r"(?:required\s+documents?[^.]{0,120}\b)?(?:official\s+)?(?:academic\s+)?transcript\s+(?:is\s+)?required",
            r"(?:official\s+)?(?:academic\s+)?transcript\s+(?:is\s+)?required",
            r"transcript\s+(?:must\s+be\s+)?(?:submitted|uploaded|provided)",
            r"university\s+transcript\s+(?:is\s+)?required",
            r"applicants?\s+(?:must|should)\s+(?:submit|provide|upload)\s+(?:an?\s+)?(?:official\s+)?transcript",
        )
    ),
    formatter="Academic transcript required",
    is_boolean=True,
)

_CV_SPECS = _PatternSpec(
    field="cv",
    req_type="cv",
    patterns=_compile(
        (
            r"(?:required\s+documents?[^.]{0,120}\b)?(?:CV|curriculum\s+vitae|resume)\s+(?:is\s+)?required",
            r"(?:CV|curriculum\s+vitae|resume)\s+(?:is\s+)?required",
            r"submit\s+(?:a\s+)?(?:(?:current|updated|recent)\s+)?(?:CV|curriculum\s+vitae|resume)",
            r"(?:CV|curriculum\s+vitae|resume)\s+with\s+your\s+application",
            r"applicants?\s+(?:must|should)\s+(?:submit|provide|upload)\s+(?:a\s+)?(?:CV|curriculum\s+vitae|resume)",
        )
    ),
    formatter="CV / Resume required",
    is_boolean=True,
)

_SOP_SPECS = _PatternSpec(
    field="statement_of_purpose",
    req_type="statement_of_purpose",
    patterns=_compile(
        (
            r"(?:required\s+documents?[^.]{0,120}\b)?statement\s+of\s+purpose\s+(?:is\s+)?required",
            r"statement\s+of\s+purpose\s+(?:is\s+)?required",
            r"(?:personal\s+)?statement\s+(?:of\s+purpose\s+)?(?:is\s+)?required",
            r"applicants?\s+(?:must|should)\s+(?:submit|provide|upload)\s+(?:a\s+)?statement\s+of\s+purpose",
        )
    ),
    formatter="Statement of purpose required",
    is_boolean=True,
)

_MOTIVATION_LETTER_SPECS = _PatternSpec(
    field="motivation_letter",
    req_type="motivation_letter",
    patterns=_compile(
        (
            r"(?:required\s+documents?[^.]{0,120}\b)?motivation\s+letter\s+(?:is\s+)?required",
            r"motivation\s+letter\s+(?:is\s+)?required",
            r"letter\s+of\s+motivation\s+(?:is\s+)?required",
            r"applicants?\s+(?:must|should)\s+(?:submit|provide|upload)\s+(?:a\s+)?(?:motivation\s+letter|letter\s+of\s+motivation)",
        )
    ),
    formatter="Motivation letter required",
    is_boolean=True,
)

_DEGREE_SPECS = _PatternSpec(
    field="degree",
    req_type="degree",
    patterns=_compile(
        (
            r"(?:minimum|min\.?)\s*(?:of\s+)?(?:a\s+)?((?:bachelor|master|doctoral|ph\.?d|undergraduate|graduate|associate)[\w\s'-]{0,24}?degree)",
            r"((?:bachelor|master|doctoral|ph\.?d|undergraduate|graduate|associate)[\w\s'-]{0,24}?degree)\s+(?:is\s+)?required",
            r"(?:applicants?|candidates?)\s+(?:must|should)\s+hold\s+(?:a\s+)?((?:bachelor|master|doctoral|ph\.?d|undergraduate|graduate|associate)[\w\s'-]{0,24}?degree)",
            r"(?:academic\s+background|eligibility)[^.]{0,80}?"
            r"((?:bachelor|master|doctoral|ph\.?d|undergraduate|graduate|associate)[\w\s'-]{0,24}?degree)",
            r"\b(bachelor(?:'s)?|undergraduate|master(?:'s)?|doctoral|doctorate|ph\.?d|associate)\s+(?:degree|qualification)\b",
            r"(?:must|should)\s+(?:have|hold|possess)\s+(?:a\s+)?((?:bachelor|master|doctoral|ph\.?d|undergraduate|graduate|associate)[\w\s'-]{0,24}?degree)",
        )
    ),
    formatter="Required degree: {value}",
    value_from_group=_text_from_group(1, normalizer=_normalize_degree),
)

_MAJOR_SPECS = _PatternSpec(
    field="major",
    req_type="major",
    patterns=_compile(
        (
            r"(?:major|field\s+of\s+study)\s+(?:in|of)\s+([A-Za-z][\w\s/&-]{2,40})",
            r"studying\s+([A-Za-z][\w\s/&-]{2,40})\s+(?:is\s+)?(?:required|preferred|expected)",
            r"(?:academic\s+background|eligibility)[^.]{0,80}?"
            r"(?:major(?:ing)?\s+in|field\s+of\s+study)\s+([A-Za-z][\w\s/&-]{2,40})",
            r"(?:applicants?|candidates?)\s+(?:must|should)\s+(?:be\s+)?(?:major(?:ing)?\s+in|studying)\s+([A-Za-z][\w\s/&-]{2,40})",
        )
    ),
    formatter="Required major/field: {value}",
    value_from_group=_text_from_group(1, normalizer=_normalize_major),
)

_NATIONALITY_SPECS = _PatternSpec(
    field="nationality",
    req_type="nationality",
    patterns=_compile(
        (
            r"(?:citizens?|nationals?)\s+of\s+([A-Za-z][\w\s,&-]{2,80})",
            r"(?:nationality|citizenship)\s*(?:\:)?\s*([A-Za-z][\w\s,&-]{2,80})",
            r"(?:applicants?|candidates?)\s+from\s+([A-Za-z][\w\s,&-]{2,80})",
            r"eligible\s+(?:applicants?|candidates?)\s+(?:include\s+)?(?:citizens?|nationals?)\s+of\s+([A-Za-z][\w\s,&-]{2,80})",
        )
    ),
    formatter="Eligible nationality: {value}",
    value_from_group=_text_from_group(1, normalizer=_normalize_country_list),
)

_COUNTRY_ELIGIBILITY_SPECS = _PatternSpec(
    field="country_eligibility",
    req_type="country",
    patterns=_compile(
        (
            r"eligible\s+countries?\s*(?:\:)?\s*([A-Za-z][\w\s,&-]{2,120})",
            r"(?:applicants?|candidates?)\s+from\s+([A-Za-z][\w\s,&-]{2,120})\s+(?:only|are\s+eligible|may\s+apply|can\s+apply)",
            r"must\s+be\s+(?:a\s+)?resident\s+of\s+([A-Za-z][\w\s,&-]{2,80})",
            r"(?:applicants?|candidates?)\s+(?:must|should)\s+(?:be\s+)?(?:from|residing\s+in)\s+([A-Za-z][\w\s,&-]{2,80})",
        )
    ),
    formatter="Country eligibility: {value}",
    value_from_group=_text_from_group(1, normalizer=_normalize_country_list),
)

_ENGLISH_SPECS = _PatternSpec(
    field="english_requirement",
    req_type="english_requirement",
    patterns=_compile(
        (
            r"english\s+(?:language\s+)?proficiency\s+(?:is\s+)?required",
            r"(?:language\s+requirement|language\s+requirements)[^.]{0,80}?english",
            r"demonstrate\s+english\s+(?:language\s+)?proficiency",
            r"proof\s+of\s+english\s+(?:language\s+)?(?:proficiency|ability)",
            r"(?:applicants?|candidates?)\s+(?:must|should)\s+demonstrate\s+english\s+(?:language\s+)?proficiency",
        )
    ),
    formatter="English language proficiency required",
    is_boolean=True,
)

_GRADUATION_CERT_SPECS = _PatternSpec(
    field="graduation_certificate",
    req_type="graduation_certificate",
    patterns=_compile(
        (
            r"(?:required\s+documents?[^.]{0,120}\b)?(?:degree|diploma|graduation)\s+certificate\s+(?:is\s+)?required",
            r"(?:degree|diploma|graduation)\s+certificate\s+(?:is\s+)?required",
            r"copy\s+of\s+(?:your\s+)?(?:degree|diploma)",
            r"applicants?\s+(?:must|should)\s+(?:submit|provide|upload)\s+(?:a\s+)?(?:degree|diploma|graduation)\s+certificate",
        )
    ),
    formatter="Graduation / degree certificate required",
    is_boolean=True,
)

_WORK_EXPERIENCE_SPECS = _PatternSpec(
    field="work_experience",
    req_type="work_experience",
    patterns=_compile(
        (
            rf"(?:minimum|min\.?|at\s+least)\s+(\d+|{_WORD_NUMBER_PATTERN})\+?\s*(?:years?\s+of\s+)?(?:relevant\s+)?work\s+experience",
            rf"(\d+|{_WORD_NUMBER_PATTERN})\+?\s*(?:years?\s+of\s+)?(?:relevant\s+)?work\s+experience",
            rf"minimum\s+of\s+(\d+|{_WORD_NUMBER_PATTERN})\s+years?\s+(?:of\s+)?work\s+experience",
            r"(?:applicants?|candidates?)\s+(?:must|should)\s+have\s+(?:at\s+least\s+)?(\d+)\s+years?\s+(?:of\s+)?(?:relevant\s+)?(?:work\s+)?experience",
        )
    ),
    formatter="Minimum work experience (years): {value}",
    operator=">=",
    value_from_group=_count_from_group(1),
)

_PUBLICATIONS_SPECS = _PatternSpec(
    field="publications",
    req_type="publications",
    patterns=_compile(
        (
            r"publications?\s+(?:are\s+)?required",
            rf"at\s+least\s+(\d+|{_WORD_NUMBER_PATTERN})\s+publications?",
            r"published\s+research\s+(?:is\s+)?required",
            r"(?:applicants?|candidates?)\s+(?:must|should)\s+have\s+(?:peer-reviewed\s+)?publications?",
        )
    ),
    formatter="Publications required: {value}",
    operator=">=",
    value_from_group=_count_from_group(1),
)

_RESEARCH_PROPOSAL_SPECS = _PatternSpec(
    field="research_proposal",
    req_type="research_proposal",
    patterns=_compile(
        (
            r"(?:required\s+documents?[^.]{0,120}\b)?research\s+proposal\s+(?:is\s+)?required",
            r"research\s+proposal\s+(?:is\s+)?required",
            r"submit\s+(?:a\s+)?research\s+proposal",
            r"applicants?\s+(?:must|should)\s+(?:submit|provide|upload)\s+(?:a\s+)?research\s+proposal",
        )
    ),
    formatter="Research proposal required",
    is_boolean=True,
)

_FINANCIAL_SPECS = _PatternSpec(
    field="financial_documents",
    req_type="financial_documents",
    patterns=_compile(
        (
            r"(?:required\s+documents?[^.]{0,120}\b)?(?:proof\s+of\s+)?(?:financial\s+)?(?:support|solvency|resources)\s+(?:is\s+)?required",
            r"(?:proof\s+of\s+)?(?:financial\s+)?(?:support|solvency|resources)\s+(?:is\s+)?required",
            r"bank\s+statement\s+(?:is\s+)?required",
            r"financial\s+documents?\s+(?:are\s+)?required",
            r"applicants?\s+(?:must|should)\s+(?:provide|submit)\s+(?:proof\s+of\s+)?financial\s+(?:support|documents?)",
        )
    ),
    formatter="Financial documents required",
    is_boolean=True,
)

_VISA_SPECS = _PatternSpec(
    field="visa",
    req_type="visa",
    patterns=_compile(
        (
            r"(?:required\s+documents?[^.]{0,120}\b)?(?:valid\s+)?visa\s+(?:is\s+)?required",
            r"(?:valid\s+)?visa\s+(?:is\s+)?required",
            r"student\s+visa\s+(?:is\s+)?required",
            r"copy\s+of\s+(?:your\s+)?visa",
            r"visa\s+requirements?\s+(?:apply|must\s+be\s+met)",
        )
    ),
    formatter="Visa required",
    is_boolean=True,
)

_APPLICATION_DEADLINE_SPECS = _PatternSpec(
    field="application_deadline",
    req_type="application_deadline",
    patterns=_compile(
        (
            r"application\s+deadline\s*(?:is|:)?\s*([A-Za-z0-9,\s/-]{4,40})",
            r"deadline\s*(?:for\s+applications?)?\s*(?:is|:)?\s*([A-Za-z0-9,\s/-]{4,40})",
            r"apply\s+by\s+([A-Za-z0-9,\s/-]{4,40})",
            r"closing\s+date\s*(?:is|:)?\s*([A-Za-z0-9,\s/-]{4,40})",
            r"submissions?\s+(?:must\s+be\s+)?(?:received\s+)?by\s+([A-Za-z0-9,\s/-]{4,40})",
        )
    ),
    formatter="Application deadline: {value}",
    value_from_group=_text_from_group(1, normalizer=_normalize_deadline),
)

_REQUIRED_DOCUMENTS_SECTION = re.compile(
    r"(?:required\s+documents?|documents?\s+required|supporting\s+documents?)"
    r"\s*(?:include|:)?\s*([^.;\n]{10,500})",
    re.IGNORECASE,
)

_ALL_SPECS: tuple[_PatternSpec, ...] = (
    _GPA_SPECS,
    _IELTS_SPECS,
    _TOEFL_SPECS,
    _DUOLINGO_SPECS,
    _ENGLISH_SPECS,
    _PASSPORT_SPECS,
    _RECOMMENDATION_SPECS,
    _TRANSCRIPT_SPECS,
    _CV_SPECS,
    _SOP_SPECS,
    _MOTIVATION_LETTER_SPECS,
    _DEGREE_SPECS,
    _MAJOR_SPECS,
    _NATIONALITY_SPECS,
    _COUNTRY_ELIGIBILITY_SPECS,
    _GRADUATION_CERT_SPECS,
    _WORK_EXPERIENCE_SPECS,
    _PUBLICATIONS_SPECS,
    _RESEARCH_PROPOSAL_SPECS,
    _FINANCIAL_SPECS,
    _VISA_SPECS,
    _APPLICATION_DEADLINE_SPECS,
)


def _format_display_value(spec: _PatternSpec, normalized: Any) -> str:
    if spec.is_boolean:
        return spec.formatter if "{value}" not in spec.formatter else spec.formatter.format(value="required")
    if normalized is None or normalized is True:
        return spec.formatter.format(value="required")
    if isinstance(normalized, list):
        return spec.formatter.format(value=", ".join(str(item) for item in normalized))
    return spec.formatter.format(value=normalized)


def _extract_from_text(
    text: str,
    spec: _PatternSpec,
    *,
    source: str,
) -> RetrievedRequirement | None:
    for pattern in spec.patterns:
        match = pattern.search(text)
        if not match:
            continue

        if spec.is_boolean:
            normalized: Any = True
        elif spec.value_from_group is not None:
            normalized = spec.value_from_group(match)
            if normalized is None and spec.field == "publications":
                normalized = True
            elif normalized is None and not spec.is_boolean:
                continue
        else:
            normalized = match.group(1) if match.lastindex else None
            if normalized is None:
                continue

        if spec.field == "nationality" and isinstance(normalized, list) and len(normalized) == 1:
            normalized = normalized[0]

        display = _format_display_value(spec, normalized)
        structured = _build_structured(
            spec.req_type,
            operator=spec.operator,
            value=normalized,
        )

        start = max(0, match.start() - 40)
        end = min(len(text), match.end() + 40)
        excerpt = text[start:end].strip()

        return RetrievedRequirement(
            field=spec.field,
            value=display,
            source=source,
            excerpt=excerpt,
            structured=structured,
        )

    return None


def _extract_required_documents_section(
    text: str,
    *,
    source: str,
) -> RetrievedRequirement | None:
    match = _REQUIRED_DOCUMENTS_SECTION.search(text)
    if not match:
        return None

    section = match.group(1)
    found_docs: list[str] = []
    for pattern, doc_type in _DOCUMENT_KEYWORDS:
        if pattern.search(section) and doc_type not in found_docs:
            found_docs.append(doc_type)

    if not found_docs:
        return None

    excerpt_start = max(0, match.start() - 20)
    excerpt_end = min(len(text), match.end() + 40)
    display = f"Required documents: {', '.join(found_docs)}"

    return RetrievedRequirement(
        field="required_documents",
        value=display,
        source=source,
        excerpt=text[excerpt_start:excerpt_end].strip(),
        structured=_build_structured("required_documents", value=found_docs),
    )


def extract_requirements_from_documents(
    documents: list[Document],
) -> list[RetrievedRequirement]:
    """
    Scan retrieved KB chunks and extract requirement values.

    When both static and application sources mention the same field,
    the application (dynamic) source takes precedence.
    """
    found: dict[str, RetrievedRequirement] = {}

    # Process static first, then application so dynamic KB overrides static.
    sorted_docs = sorted(
        documents,
        key=lambda doc: (doc.metadata or {}).get("retrieved_from", "static") == "application",
    )

    for document in sorted_docs:
        metadata = document.metadata or {}
        source = metadata.get("retrieved_from", metadata.get("knowledge_source", "unknown"))
        text = document.page_content.strip()
        if not text:
            continue

        for spec in _ALL_SPECS:
            extracted = _extract_from_text(text, spec, source=str(source))
            if extracted:
                found[spec.field] = extracted

        documents_section = _extract_required_documents_section(text, source=str(source))
        if documents_section:
            found["required_documents"] = documents_section

    return list(found.values())
