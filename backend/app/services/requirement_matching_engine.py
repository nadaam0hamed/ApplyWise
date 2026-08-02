"""Deterministic requirement matching engine.

Retrieves scholarship requirements from static and dynamic knowledge bases via
``HybridRetriever``, extracts concrete values with regex, and compares them
against the extracted ``ApplicantProfile`` using rule-based logic only.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from enum import StrEnum
from typing import Sequence

from app.chains.extraction_parser import ApplicantProfile
from app.models import Document, Requirement
from app.rag.retriever import HybridRetriever
from app.schemas.requirement_matching import (
    FieldComparison,
    MatchStatus,
    RequirementMatchingResult,
    RetrievedRequirement,
    normalized_numeric_value,
)
from app.services.requirement_extractor import extract_requirements_from_documents
from app.utils.config import Settings, get_settings

_FIELD_RETRIEVAL_QUERIES: dict[str, str] = {
    "gpa": "minimum GPA grade point average academic requirement eligibility",
    "degree": "minimum degree level bachelor master doctoral requirement",
    "major": "major field of study discipline requirement",
    "nationality": "nationality citizenship eligible applicants requirement",
    "country_eligibility": "eligible countries residency country requirement",
    "ielts": "IELTS language proficiency minimum overall band score requirement",
    "toefl": "TOEFL iBT minimum language score requirement",
    "duolingo": "Duolingo English Test DET minimum score requirement",
    "english_requirement": "English language proficiency requirement",
    "application_deadline": "application deadline closing date apply by requirement",
    "required_documents": "required documents supporting documents upload requirement",
    "passport": "passport identity document valid requirement",
    "recommendation_letters": "recommendation letter reference count requirement",
    "transcript": "academic transcript official university requirement",
    "graduation_certificate": "degree diploma graduation certificate requirement",
    "cv": "CV resume curriculum vitae requirement",
    "statement_of_purpose": "statement of purpose motivation letter personal statement requirement",
    "motivation_letter": "motivation letter requirement",
    "work_experience": "work experience years professional experience requirement",
    "publications": "publications research papers requirement",
    "research_proposal": "research proposal requirement",
    "financial_documents": "financial proof bank statement requirement",
    "visa": "visa student visa requirement",
}

_DEGREE_ALIASES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"associate", re.IGNORECASE), "Associate"),
    (re.compile(r"bachelor|undergraduate|b\.?\s*sc|b\.?\s*a", re.IGNORECASE), "Bachelor"),
    (re.compile(r"master(?:'?s)?(?!\s+of\s+business)|m\.?\s*sc|m\.?\s*a", re.IGNORECASE), "Master"),
    (re.compile(r"mba|master\s+of\s+business", re.IGNORECASE), "MBA"),
    (re.compile(r"doctoral|doctorate|ph\.?\s*d", re.IGNORECASE), "Doctoral"),
)

_DEGREE_RANK: dict[str, int] = {
    "Associate": 1,
    "Bachelor": 2,
    "Master": 3,
    "MBA": 3,
    "Doctoral": 4,
}

_REQUIRED_DOC_TYPE_MAP: dict[str, tuple[str, ...]] = {
    "passport": ("passport",),
    "academic_transcript": ("academic_transcript",),
    "transcript": ("academic_transcript",),
    "cv": ("cv",),
    "statement_of_purpose": ("statement_of_purpose", "motivation_letter"),
    "motivation_letter": ("motivation_letter", "statement_of_purpose"),
    "recommendation_letters": ("letter_of_recommendation",),
    "graduation_certificate": ("diploma",),
    "ielts_score": ("ielts_score",),
    "toefl_score": ("toefl_score",),
    "research_proposal": ("other",),
    "financial_documents": ("other",),
    "visa": ("other",),
}

_REQUIRED_DOC_FILENAME_KEYWORDS: dict[str, tuple[str, ...]] = {
    "research_proposal": ("research", "proposal"),
    "financial_documents": ("bank", "financial", "funds", "sponsor"),
    "visa": ("visa",),
}


class _RuleKind(StrEnum):
    NUMERIC = "numeric"
    COUNT = "count"
    DOCUMENT = "document"
    TEXT = "text"
    PRESENCE = "presence"


def _compute_rule_confidence(
    status: MatchStatus,
    *,
    kind: _RuleKind,
    has_requirement: bool,
    has_applicant: bool,
) -> float:
    """Compute confidence from deterministic rule outcome."""
    if not has_requirement:
        return 0.2

    if status == MatchStatus.UNKNOWN:
        return 0.2

    if kind in {_RuleKind.NUMERIC, _RuleKind.COUNT, _RuleKind.DOCUMENT, _RuleKind.PRESENCE}:
        if status == MatchStatus.PARTIAL:
            return 0.8
        return 1.0

    if kind == _RuleKind.TEXT:
        if status == MatchStatus.PARTIAL:
            return 0.8
        return 1.0

    return 0.5


def _build_comparison(
    *,
    field: str,
    requirement: str | None,
    applicant: str | None,
    status: MatchStatus,
    reason: str,
    kind: _RuleKind,
    knowledge_source: str | None = None,
    suggested_action: str | None = None,
) -> FieldComparison:
    has_requirement = requirement is not None
    has_applicant = applicant is not None
    confidence = _compute_rule_confidence(
        status,
        kind=kind,
        has_requirement=has_requirement,
        has_applicant=has_applicant,
    )
    return FieldComparison(
        field=field,
        requirement=requirement,
        applicant=applicant,
        status=status,
        reason=reason,
        confidence=confidence,
        suggested_action=suggested_action,
        knowledge_source=knowledge_source,
    )


def _suggested_action_for(comparison: FieldComparison) -> str | None:
    field_key = comparison.field.lower()
    status = comparison.status

    if status == MatchStatus.PASS:
        return None

    if "gpa" in field_key:
        if status == MatchStatus.FAIL:
            return "Not eligible unless the program allows exceptions."
        return "Confirm your official transcript shows GPA clearly and matches the required scale."

    if "ielts" in field_key:
        if comparison.applicant and "not extracted" in comparison.applicant.lower():
            return "Upload a complete IELTS score report."
        if status in {MatchStatus.FAIL, MatchStatus.PARTIAL}:
            target = comparison.requirement or "the required minimum"
            return f"Retake IELTS and aim for at least {target}."
        return "Upload a complete IELTS score report."

    if "toefl" in field_key:
        if comparison.applicant and "not extracted" in comparison.applicant.lower():
            return "Upload a complete TOEFL score report."
        if status in {MatchStatus.FAIL, MatchStatus.PARTIAL}:
            target = comparison.requirement or "the required minimum"
            return f"Retake TOEFL and aim for at least {target}."
        return "Upload a complete TOEFL score report."

    if "duolingo" in field_key:
        if comparison.applicant and "not extracted" in comparison.applicant.lower():
            return "Upload a complete Duolingo English Test score report."
        if status in {MatchStatus.FAIL, MatchStatus.PARTIAL}:
            target = comparison.requirement or "the required minimum"
            return f"Retake Duolingo English Test and aim for at least {target}."
        return "Upload a complete Duolingo English Test score report."

    if "english requirement" in field_key:
        if status == MatchStatus.FAIL:
            return "Take an approved English proficiency test and upload the score report."
        return "Upload English proficiency evidence or confirm accepted test types."

    if "passport" in field_key:
        return "Upload a valid passport with readable identity and expiry details."

    if "recommendation" in field_key:
        if status == MatchStatus.PARTIAL and comparison.requirement and comparison.applicant:
            req_match = re.search(r"(\d+)", comparison.requirement)
            app_match = re.search(r"(\d+)", comparison.applicant)
            if req_match and app_match:
                missing = int(req_match.group(1)) - int(app_match.group(1))
                if missing == 1:
                    return "Request one additional recommendation letter."
                if missing > 1:
                    return f"Request {missing} additional recommendation letters."
        if status == MatchStatus.FAIL:
            return "Request recommendation letters from academic or professional referees."
        return "Request additional recommendation letters from academic or professional referees."

    if "transcript" in field_key:
        return "Upload official transcript."

    if field_key in {"cv / resume", "cv", "resume"}:
        return "Upload an updated CV or resume highlighting skills, experience, and leadership."

    if "statement of purpose" in field_key:
        return "Draft or upload your statement of purpose addressing program fit and career goals."

    if "motivation" in field_key:
        return "Draft or upload your motivation letter addressing program fit and career goals."

    if field_key == "degree":
        return "Confirm your awarded degree meets the required level or provide degree certificate evidence."

    if field_key == "major":
        return "Align your field of study with the program requirement or explain equivalency in your SOP."

    if "nationality" in field_key or "country eligibility" in field_key:
        return "Verify you meet nationality or country eligibility rules before applying."

    if "graduation" in field_key or "certificate" in field_key:
        return "Upload your graduation or degree certificate."

    if "work experience" in field_key:
        return "Add relevant internships or professional roles to your CV to meet experience requirements."

    if "publication" in field_key:
        return "List peer-reviewed or research publications on your CV or provide supporting documents."

    if "research proposal" in field_key:
        return "Prepare and upload a research proposal aligned with the scholarship objectives."

    if "financial" in field_key:
        return "Provide bank statements or financial support documents as specified by the program."

    if "visa" in field_key:
        return "Obtain or upload visa documentation if required for your application stage."

    if "required documents" in field_key:
        return "Upload all required supporting documents listed in the scholarship guidelines."

    if status == MatchStatus.UNKNOWN:
        return "Confirm this requirement in the official guidelines and upload supporting evidence."

    return "Address this gap before submission."


def _enrich_comparison(comparison: FieldComparison) -> FieldComparison:
    if comparison.status in {MatchStatus.PASS, MatchStatus.UNKNOWN}:
        if comparison.suggested_action is not None:
            return comparison.model_copy(update={"suggested_action": None})
        return comparison

    action = comparison.suggested_action or _suggested_action_for(comparison)
    if comparison.suggested_action == action:
        return comparison
    return comparison.model_copy(update={"suggested_action": action})


def _text_tokens(value: str) -> set[str]:
    return {token for token in re.split(r"[\W_]+", value.lower()) if len(token) > 2}


def _text_overlap_score(left: str | None, right: str | None) -> float:
    if not left or not right:
        return 0.0
    left_tokens = _text_tokens(left)
    right_tokens = _text_tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    overlap = left_tokens & right_tokens
    return len(overlap) / max(len(left_tokens), len(right_tokens))


def _normalize_degree_level(value: str | None) -> str | None:
    if not value:
        return None
    for pattern, label in _DEGREE_ALIASES:
        if pattern.search(value):
            return label
    return value.strip().title()


def _structured_text_values(requirement: RetrievedRequirement | None) -> list[str]:
    if requirement is None or requirement.structured is None or requirement.structured.value is None:
        return []
    raw = requirement.structured.value
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    return [str(raw).strip()]


def _applicant_degree(profile: ApplicantProfile) -> str | None:
    if profile.transcript and profile.transcript.degree:
        return profile.transcript.degree
    if profile.degree_certificate and profile.degree_certificate.degree:
        return profile.degree_certificate.degree
    return None


def _applicant_major(profile: ApplicantProfile) -> str | None:
    if profile.transcript and profile.transcript.major:
        return profile.transcript.major
    if profile.degree_certificate and profile.degree_certificate.major:
        return profile.degree_certificate.major
    return None


def _applicant_nationality(profile: ApplicantProfile) -> str | None:
    if profile.passport and profile.passport.nationality:
        return profile.passport.nationality
    return None


def _compare_degree(
    profile: ApplicantProfile,
    requirement: RetrievedRequirement | None,
) -> FieldComparison:
    applicant_value = _applicant_degree(profile)
    required_display = requirement.value if requirement else None

    if requirement is None:
        return _build_comparison(
            field="Degree",
            requirement=None,
            applicant=applicant_value,
            status=MatchStatus.UNKNOWN,
            reason="No degree requirement found in knowledge base.",
            kind=_RuleKind.TEXT,
        )

    if not applicant_value:
        return _build_comparison(
            field="Degree",
            requirement=required_display,
            applicant=None,
            status=MatchStatus.FAIL,
            reason="Degree is required but no degree information was extracted from applicant documents.",
            kind=_RuleKind.TEXT,
            knowledge_source=requirement.source,
        )

    required_level = _normalize_degree_level(_structured_text_values(requirement)[0] if _structured_text_values(requirement) else requirement.value)
    applicant_level = _normalize_degree_level(applicant_value)

    if required_level and applicant_level:
        required_rank = _DEGREE_RANK.get(required_level, 0)
        applicant_rank = _DEGREE_RANK.get(applicant_level, 0)
        if required_rank and applicant_rank:
            if applicant_rank >= required_rank:
                status = MatchStatus.PASS
                reason = f"Applicant degree ({applicant_level}) meets the minimum required level ({required_level})."
            else:
                status = MatchStatus.FAIL
                reason = (
                    f"Applicant degree ({applicant_level}) is below the required level ({required_level})."
                )
            return _build_comparison(
                field="Degree",
                requirement=required_level,
                applicant=applicant_level,
                status=status,
                reason=reason,
                kind=_RuleKind.TEXT,
                knowledge_source=requirement.source,
            )

    target = requirement.excerpt if requirement.excerpt else requirement.value
    score = _text_overlap_score(applicant_value, target)
    if score >= 0.35 or applicant_value.lower() in target.lower() or target.lower() in applicant_value.lower():
        status = MatchStatus.PASS
        reason = "Applicant degree aligns with the scholarship requirement."
    elif score >= 0.15:
        status = MatchStatus.PARTIAL
        reason = f"Applicant degree ({applicant_value}) only partially matches the requirement ({required_display})."
    else:
        status = MatchStatus.FAIL
        reason = f"Applicant degree ({applicant_value}) does not match the requirement ({required_display})."

    return _build_comparison(
        field="Degree",
        requirement=required_display,
        applicant=applicant_value,
        status=status,
        reason=reason,
        kind=_RuleKind.TEXT,
        knowledge_source=requirement.source,
    )


def _compare_major(
    profile: ApplicantProfile,
    requirement: RetrievedRequirement | None,
) -> FieldComparison:
    return _compare_structured_text(
        field_label="Major",
        requirement=requirement,
        applicant_value=_applicant_major(profile),
    )


def _compare_nationality_or_country(
    *,
    field_label: str,
    requirement: RetrievedRequirement | None,
    applicant_value: str | None,
) -> FieldComparison:
    required_display = requirement.value if requirement else None

    if requirement is None:
        return _build_comparison(
            field=field_label,
            requirement=None,
            applicant=applicant_value,
            status=MatchStatus.UNKNOWN,
            reason=f"No {field_label.lower()} requirement found in knowledge base.",
            kind=_RuleKind.TEXT,
        )

    if not applicant_value:
        return _build_comparison(
            field=field_label,
            requirement=required_display,
            applicant=None,
            status=MatchStatus.FAIL,
            reason=f"{field_label} requirement found but applicant nationality was not extracted.",
            kind=_RuleKind.TEXT,
            knowledge_source=requirement.source,
        )

    allowed = _structured_text_values(requirement)
    if not allowed:
        target = requirement.excerpt if requirement.excerpt else requirement.value
        allowed = [target]

    applicant_lower = applicant_value.lower()
    matched = any(
        applicant_lower == candidate.lower()
        or applicant_lower in candidate.lower()
        or candidate.lower() in applicant_lower
        for candidate in allowed
    )

    if matched:
        status = MatchStatus.PASS
        reason = f"Applicant nationality ({applicant_value}) meets the {field_label.lower()} requirement."
    else:
        status = MatchStatus.FAIL
        reason = (
            f"Applicant nationality ({applicant_value}) does not match "
            f"the stated {field_label.lower()} requirement ({required_display})."
        )

    return _build_comparison(
        field=field_label,
        requirement=required_display,
        applicant=applicant_value,
        status=status,
        reason=reason,
        kind=_RuleKind.TEXT,
        knowledge_source=requirement.source,
    )


def _compare_structured_text(
    *,
    field_label: str,
    requirement: RetrievedRequirement | None,
    applicant_value: str | None,
    requirement_label: str | None = None,
) -> FieldComparison:
    required_display = requirement.value if requirement else requirement_label

    if requirement is None and not requirement_label:
        return _build_comparison(
            field=field_label,
            requirement=None,
            applicant=applicant_value,
            status=MatchStatus.UNKNOWN,
            reason=f"No {field_label.lower()} requirement found in knowledge base.",
            kind=_RuleKind.TEXT,
        )

    if not applicant_value:
        return _build_comparison(
            field=field_label,
            requirement=required_display,
            applicant=None,
            status=MatchStatus.FAIL,
            reason=f"{field_label} requirement found but applicant value was not extracted.",
            kind=_RuleKind.TEXT,
            knowledge_source=requirement.source if requirement else None,
        )

    structured_targets = _structured_text_values(requirement)
    target = structured_targets[0] if structured_targets else (
        requirement.excerpt if requirement and requirement.excerpt else (requirement.value if requirement else "")
    )

    if structured_targets:
        applicant_lower = applicant_value.lower()
        matched = any(
            applicant_lower == candidate.lower()
            or applicant_lower in candidate.lower()
            or candidate.lower() in applicant_lower
            for candidate in structured_targets
        )
        if matched:
            status = MatchStatus.PASS
            reason = f"Applicant {field_label.lower()} ({applicant_value}) matches the requirement."
        else:
            score = max(_text_overlap_score(applicant_value, candidate) for candidate in structured_targets)
            if score >= 0.35:
                status = MatchStatus.PARTIAL
                reason = (
                    f"Applicant {field_label.lower()} ({applicant_value}) partially matches "
                    f"the requirement ({required_display})."
                )
            else:
                status = MatchStatus.FAIL
                reason = (
                    f"Applicant {field_label.lower()} ({applicant_value}) does not match "
                    f"the requirement ({required_display})."
                )
    else:
        score = _text_overlap_score(applicant_value, target)
        if score >= 0.35 or applicant_value.lower() in target.lower() or target.lower() in applicant_value.lower():
            status = MatchStatus.PASS
            reason = f"Applicant {field_label.lower()} aligns with the scholarship requirement."
        elif score >= 0.15:
            status = MatchStatus.PARTIAL
            reason = (
                f"Applicant {field_label.lower()} ({applicant_value}) only partially matches "
                f"the stated requirement ({required_display})."
            )
        else:
            status = MatchStatus.FAIL
            reason = (
                f"Applicant {field_label.lower()} ({applicant_value}) does not match "
                f"the stated requirement ({required_display})."
            )

    return _build_comparison(
        field=field_label,
        requirement=required_display,
        applicant=applicant_value,
        status=status,
        reason=reason,
        kind=_RuleKind.TEXT,
        knowledge_source=requirement.source if requirement else None,
    )


def _compare_numeric_threshold(
    *,
    field_label: str,
    requirement: RetrievedRequirement | None,
    applicant_numeric: float | None,
    applicant_display: str | None,
    partial_tolerance: float = 0.0,
    fail_action: str | None = None,
    missing_applicant_reason: str | None = None,
    unparseable_reason: str | None = None,
) -> FieldComparison:
    required_display = requirement.value if requirement else None

    if requirement is None:
        return _build_comparison(
            field=field_label,
            requirement=None,
            applicant=applicant_display,
            status=MatchStatus.UNKNOWN,
            reason=f"No {field_label} requirement found in knowledge base.",
            kind=_RuleKind.NUMERIC,
        )

    required_value = _parse_requirement_number(requirement)
    if required_value is not None:
        required_display = str(required_value)

    if applicant_numeric is None:
        reason = missing_applicant_reason or (
            f"{field_label} requirement found but applicant value was not extracted."
        )
        return _build_comparison(
            field=field_label,
            requirement=required_display,
            applicant=applicant_display,
            status=MatchStatus.UNKNOWN,
            reason=reason,
            kind=_RuleKind.NUMERIC,
            knowledge_source=requirement.source,
        )

    if required_value is None:
        reason = unparseable_reason or (
            f"{field_label} values could not be parsed for numeric comparison."
        )
        return _build_comparison(
            field=field_label,
            requirement=required_display,
            applicant=applicant_display,
            status=MatchStatus.UNKNOWN,
            reason=reason,
            kind=_RuleKind.NUMERIC,
            knowledge_source=requirement.source,
        )

    applicant_display = applicant_display or str(applicant_numeric)

    if applicant_numeric >= required_value:
        status = MatchStatus.PASS
        reason = f"Applicant {field_label} ({applicant_numeric}) meets or exceeds the minimum ({required_value})."
    elif partial_tolerance > 0 and applicant_numeric >= required_value - partial_tolerance:
        status = MatchStatus.PARTIAL
        reason = (
            f"Applicant {field_label} ({applicant_numeric}) is below the minimum ({required_value}) "
            f"but within the partial tolerance ({partial_tolerance})."
        )
    else:
        status = MatchStatus.FAIL
        reason = f"Applicant {field_label} ({applicant_numeric}) is below the requirement ({required_value})."

    return _build_comparison(
        field=field_label,
        requirement=required_display,
        applicant=applicant_display,
        status=status,
        reason=reason,
        kind=_RuleKind.NUMERIC,
        knowledge_source=requirement.source,
        suggested_action=fail_action if status == MatchStatus.FAIL else None,
    )


def _compare_count_requirement(
    *,
    field_label: str,
    requirement: RetrievedRequirement | None,
    applicant_count: int,
    applicant_display: str,
    item_label: str = "item(s)",
) -> FieldComparison:
    if requirement is None:
        return _build_comparison(
            field=field_label,
            requirement=None,
            applicant=applicant_display,
            status=MatchStatus.UNKNOWN,
            reason=f"No {field_label.lower()} requirement found in knowledge base.",
            kind=_RuleKind.COUNT,
        )

    required_count = _parse_requirement_number(requirement)
    if required_count is None:
        required_count = _parse_float(requirement.value)

    if required_count is None:
        if applicant_count > 0:
            status = MatchStatus.PARTIAL
            reason = (
                f"{field_label} evidence found ({applicant_count} {item_label}) "
                f"but the required count could not be parsed for numeric comparison."
            )
        else:
            status = MatchStatus.UNKNOWN
            reason = f"{field_label} count could not be parsed from requirement text."
        return _build_comparison(
            field=field_label,
            requirement=requirement.value,
            applicant=applicant_display,
            status=status,
            reason=reason,
            kind=_RuleKind.COUNT,
            knowledge_source=requirement.source,
        )

    required_int = int(required_count)
    required_display = str(required_int)

    if applicant_count >= required_int:
        status = MatchStatus.PASS
        reason = f"Applicant has {applicant_count} {item_label}; {required_int} required."
    elif applicant_count > 0:
        status = MatchStatus.PARTIAL
        reason = f"Applicant has {applicant_count} {item_label} but {required_int} are required."
    else:
        status = MatchStatus.FAIL
        reason = f"No {item_label} found; {required_int} required."

    return _build_comparison(
        field=field_label,
        requirement=required_display,
        applicant=applicant_display,
        status=status,
        reason=reason,
        kind=_RuleKind.COUNT,
        knowledge_source=requirement.source,
    )


def _compare_english_requirement(
    profile: ApplicantProfile,
    documents: Sequence[Document],
    requirement: RetrievedRequirement | None,
    req_map: dict[str, RetrievedRequirement],
) -> FieldComparison:
    if req_map.get("ielts") or req_map.get("toefl") or req_map.get("duolingo"):
        return _build_comparison(
            field="English Requirement",
            requirement=None,
            applicant=None,
            status=MatchStatus.UNKNOWN,
            reason="Specific language test thresholds apply; see IELTS/TOEFL/Duolingo rows.",
            kind=_RuleKind.PRESENCE,
        )

    language_test = profile.language_test
    has_score_doc = _has_uploaded_document(
        documents,
        "ielts_score",
        alternate_types=("toefl_score",),
    )
    applicant_value = None
    if language_test and language_test.overall_score:
        applicant_value = f"{language_test.test_type or 'English test'} {language_test.overall_score}"

    if requirement is None:
        return _build_comparison(
            field="English Requirement",
            requirement=None,
            applicant=applicant_value,
            status=MatchStatus.UNKNOWN,
            reason="No English proficiency requirement found in knowledge base.",
            kind=_RuleKind.PRESENCE,
        )

    if applicant_value or has_score_doc:
        return _build_comparison(
            field="English Requirement",
            requirement=requirement.value,
            applicant=applicant_value or "English score document uploaded",
            status=MatchStatus.PASS,
            reason="English proficiency evidence is on file.",
            kind=_RuleKind.PRESENCE,
            knowledge_source=requirement.source,
        )

    return _build_comparison(
        field="English Requirement",
        requirement=requirement.value,
        applicant="Not uploaded",
        status=MatchStatus.FAIL,
        reason="English proficiency is required but no test scores were extracted.",
        kind=_RuleKind.PRESENCE,
        knowledge_source=requirement.source,
    )


def _estimate_work_experience_years(profile: ApplicantProfile) -> float | None:
    if not profile.cv or not profile.cv.experience:
        return None
    total = 0.0
    found_numeric = False
    for entry in profile.cv.experience:
        match = re.search(r"(\d+)\s*(?:\+?\s*)?years?", entry, re.IGNORECASE)
        if match:
            total += float(match.group(1))
            found_numeric = True
    if found_numeric:
        return total
    return float(len(profile.cv.experience))


def _compare_work_experience(
    profile: ApplicantProfile,
    documents: Sequence[Document],
    requirement: RetrievedRequirement | None,
) -> FieldComparison:
    applicant_years = _estimate_work_experience_years(profile)
    applicant_value = f"{applicant_years} years" if applicant_years is not None else None

    if requirement is None:
        return _build_comparison(
            field="Work Experience",
            requirement=None,
            applicant=applicant_value,
            status=MatchStatus.UNKNOWN,
            reason="No work experience requirement found in knowledge base.",
            kind=_RuleKind.NUMERIC,
        )

    required_years = _parse_requirement_number(requirement)
    required_display = str(int(required_years)) + " years" if required_years is not None else requirement.value

    if applicant_years is None:
        has_cv = _has_uploaded_document(documents, "cv") or bool(profile.cv)
        if not has_cv:
            return _build_comparison(
                field="Work Experience",
                requirement=required_display,
                applicant="Not uploaded",
                status=MatchStatus.FAIL,
                reason="Work experience is required but no CV was uploaded.",
                kind=_RuleKind.NUMERIC,
                knowledge_source=requirement.source,
            )
        if required_years is None:
            return _build_comparison(
                field="Work Experience",
                requirement=requirement.value,
                applicant=applicant_value,
                status=MatchStatus.FAIL,
                reason="Work experience is required but none was extracted from the CV.",
                kind=_RuleKind.NUMERIC,
                knowledge_source=requirement.source,
            )
        return _build_comparison(
            field="Work Experience",
            requirement=required_display,
            applicant=None,
            status=MatchStatus.FAIL,
            reason="Work experience is required but none was extracted from the CV.",
            kind=_RuleKind.NUMERIC,
            knowledge_source=requirement.source,
        )

    if required_years is None:
        return _build_comparison(
            field="Work Experience",
            requirement=requirement.value,
            applicant=applicant_value,
            status=MatchStatus.PARTIAL,
            reason="Work experience is mentioned as required; years could not be parsed for numeric comparison.",
            kind=_RuleKind.NUMERIC,
            knowledge_source=requirement.source,
        )

    return _compare_numeric_threshold(
        field_label="Work Experience",
        requirement=requirement,
        applicant_numeric=applicant_years,
        applicant_display=applicant_value,
        partial_tolerance=1.0,
    )


def _compare_publications(
    profile: ApplicantProfile,
    requirement: RetrievedRequirement | None,
) -> FieldComparison:
    publication_signals = 0
    if profile.cv:
        publication_signals += sum(
            1
            for item in profile.cv.projects + profile.cv.experience
            if re.search(r"publication|published|journal|paper", item, re.IGNORECASE)
        )
    applicant_value = str(publication_signals) if publication_signals else "0"

    if requirement is None:
        return _build_comparison(
            field="Publications",
            requirement=None,
            applicant=applicant_value if publication_signals else None,
            status=MatchStatus.UNKNOWN,
            reason="No publications requirement found in knowledge base.",
            kind=_RuleKind.COUNT,
        )

    required_count = _parse_requirement_number(requirement)
    if required_count is None:
        if requirement.structured and requirement.structured.value is True:
            if publication_signals > 0:
                status = MatchStatus.PASS
                reason = "Publication evidence detected on the CV."
            else:
                status = MatchStatus.FAIL
                reason = "Publications are required but none were detected."
            return _build_comparison(
                field="Publications",
                requirement=requirement.value,
                applicant=applicant_value,
                status=status,
                reason=reason,
                kind=_RuleKind.PRESENCE,
                knowledge_source=requirement.source,
            )
        if publication_signals > 0:
            status = MatchStatus.PARTIAL
            reason = (
                "Publication evidence detected on the CV but the required count "
                "could not be parsed for numeric comparison."
            )
        else:
            status = MatchStatus.UNKNOWN
            reason = "Publications may be required; numeric count could not be parsed."
        return _build_comparison(
            field="Publications",
            requirement=requirement.value,
            applicant=applicant_value if publication_signals else None,
            status=status,
            reason=reason,
            kind=_RuleKind.COUNT,
            knowledge_source=requirement.source,
        )

    return _compare_count_requirement(
        field_label="Publications",
        requirement=requirement,
        applicant_count=publication_signals,
        applicant_display=applicant_value,
        item_label="publication(s)",
    )


def _compare_application_requirement(
    requirement: Requirement,
    comparisons: list[FieldComparison],
) -> FieldComparison | None:
    title = (requirement.title or requirement.category or "Requirement").strip()
    if not title:
        return None

    normalized = title.lower()
    for comparison in comparisons:
        if comparison.field.lower() in normalized or normalized in comparison.field.lower():
            return None

    if requirement.is_fulfilled:
        status = MatchStatus.PASS
        reason = "Marked complete in the application checklist."
    elif requirement.is_required:
        status = MatchStatus.FAIL
        reason = "Required checklist item is not marked complete."
    else:
        status = MatchStatus.PARTIAL
        reason = "Optional checklist item is not marked complete."

    return _build_comparison(
        field=title,
        requirement="Required" if requirement.is_required else "Optional",
        applicant="Complete" if requirement.is_fulfilled else "Incomplete",
        status=status,
        reason=reason,
        kind=_RuleKind.PRESENCE,
        knowledge_source="application checklist",
    )


def _parse_float(value: str | None) -> float | None:
    if not value:
        return None
    match = re.search(r"(\d+\.?\d*)", value.replace(",", "."))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _parse_requirement_number(requirement: RetrievedRequirement) -> float | None:
    return normalized_numeric_value(requirement)


def _has_uploaded_document(
    documents: Sequence[Document],
    document_type: str,
    *,
    alternate_types: Sequence[str] = (),
) -> bool:
    allowed = {document_type, *alternate_types}
    return any(document.document_type in allowed for document in documents)


def _document_uploaded(
    documents: Sequence[Document],
    doc_key: str,
) -> bool:
    types = _REQUIRED_DOC_TYPE_MAP.get(doc_key, (doc_key,))
    if _has_uploaded_document(documents, types[0], alternate_types=types[1:]):
        return True
    keywords = _REQUIRED_DOC_FILENAME_KEYWORDS.get(doc_key, ())
    if keywords:
        return any(
            any(keyword in (document.file_name or "").lower() for keyword in keywords)
            for document in documents
        )
    return False


def _parse_expiry_date(raw: str | None) -> date | None:
    if not raw:
        return None

    cleaned = raw.strip()
    formats = (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%B %d, %Y",
        "%d %B %Y",
    )
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue

    year_match = re.search(r"(20\d{2})", cleaned)
    if year_match:
        month_match = re.search(
            r"(january|february|march|april|may|june|july|august|september|october|november|december)",
            cleaned,
            re.IGNORECASE,
        )
        if month_match:
            try:
                return datetime.strptime(
                    f"1 {month_match.group(1)} {year_match.group(1)}",
                    "%d %B %Y",
                ).date()
            except ValueError:
                pass

    return None


def _requirement_by_field(
    requirements: list[RetrievedRequirement],
) -> dict[str, RetrievedRequirement]:
    return {item.field: item for item in requirements}


def _compare_gpa(
    profile: ApplicantProfile,
    requirement: RetrievedRequirement | None,
) -> FieldComparison:
    applicant_gpa = profile.transcript.gpa if profile.transcript else None
    applicant_value = _parse_float(applicant_gpa)

    if requirement is not None and applicant_value is None:
        required_display = requirement.value
        parsed_required = _parse_requirement_number(requirement)
        if parsed_required is not None:
            required_display = str(parsed_required)
        return _build_comparison(
            field="Minimum GPA",
            requirement=required_display,
            applicant=None,
            status=MatchStatus.FAIL,
            reason="GPA requirement found but no GPA was extracted from applicant documents.",
            kind=_RuleKind.NUMERIC,
            knowledge_source=requirement.source,
            suggested_action="Not eligible unless the program allows exceptions.",
        )

    return _compare_numeric_threshold(
        field_label="Minimum GPA",
        requirement=requirement,
        applicant_numeric=applicant_value,
        applicant_display=str(applicant_value) if applicant_value is not None else None,
        partial_tolerance=0.2,
        fail_action="Not eligible unless the program allows exceptions.",
    )


def _compare_language_test(
    profile: ApplicantProfile,
    documents: Sequence[Document],
    *,
    field_label: str,
    requirement: RetrievedRequirement | None,
    test_name: str,
) -> FieldComparison:
    language_test = profile.language_test
    doc_type = "ielts_score" if test_name == "IELTS" else "toefl_score" if test_name == "TOEFL" else "other"
    has_doc = _has_uploaded_document(documents, doc_type)

    if language_test and language_test.test_type:
        test_type = language_test.test_type.upper()
        if test_name not in test_type:
            applicant_label = f"{test_type}: {language_test.overall_score or 'N/A'}"
            if requirement is None:
                return _build_comparison(
                    field=field_label,
                    requirement=None,
                    applicant=applicant_label,
                    status=MatchStatus.UNKNOWN,
                    reason=f"No {field_label} requirement found in knowledge base.",
                    kind=_RuleKind.NUMERIC,
                )
            return _build_comparison(
                field=field_label,
                requirement=requirement.value,
                applicant=applicant_label,
                status=MatchStatus.FAIL,
                reason=f"Applicant submitted {test_type} but requirement specifies {field_label}.",
                kind=_RuleKind.NUMERIC,
                knowledge_source=requirement.source,
            )

    overall = language_test.overall_score if language_test else None
    applicant_value = _parse_float(overall)

    if requirement is None:
        return _build_comparison(
            field=field_label,
            requirement=None,
            applicant=overall,
            status=MatchStatus.UNKNOWN,
            reason=f"No {field_label} requirement found in knowledge base.",
            kind=_RuleKind.NUMERIC,
        )

    if applicant_value is None and not has_doc:
        required_display = requirement.value
        parsed_required = _parse_requirement_number(requirement)
        if parsed_required is not None:
            required_display = str(parsed_required)
        return _build_comparison(
            field=field_label,
            requirement=required_display,
            applicant="Not uploaded",
            status=MatchStatus.FAIL,
            reason=f"{field_label} is required but no score document was uploaded.",
            kind=_RuleKind.NUMERIC,
            knowledge_source=requirement.source,
        )

    if applicant_value is None and has_doc:
        required_display = requirement.value
        parsed_required = _parse_requirement_number(requirement)
        if parsed_required is not None:
            required_display = str(parsed_required)
        return _build_comparison(
            field=field_label,
            requirement=required_display,
            applicant="Uploaded (score not extracted)",
            status=MatchStatus.PARTIAL,
            reason=f"{field_label} score document uploaded but score could not be extracted.",
            kind=_RuleKind.NUMERIC,
            knowledge_source=requirement.source,
        )

    tolerance = 0.5 if test_name in {"IELTS", "TOEFL"} else 5.0
    return _compare_numeric_threshold(
        field_label=field_label,
        requirement=requirement,
        applicant_numeric=applicant_value,
        applicant_display=str(applicant_value) if applicant_value is not None else overall,
        partial_tolerance=tolerance,
        fail_action=f"Retake {field_label}.",
        missing_applicant_reason=(
            f"{field_label} score document uploaded but score could not be extracted."
        ),
    )


def _compare_duolingo(
    profile: ApplicantProfile,
    documents: Sequence[Document],
    requirement: RetrievedRequirement | None,
) -> FieldComparison:
    language_test = profile.language_test
    has_doc = any(
        "duolingo" in (document.file_name or "").lower()
        for document in documents
    )

    overall = None
    if language_test and language_test.test_type and "DUOLINGO" in language_test.test_type.upper():
        overall = language_test.overall_score

    applicant_value = _parse_float(overall)

    if requirement is None:
        return _build_comparison(
            field="Duolingo",
            requirement=None,
            applicant=overall,
            status=MatchStatus.UNKNOWN,
            reason="No Duolingo requirement found in knowledge base.",
            kind=_RuleKind.NUMERIC,
        )

    if applicant_value is None and not has_doc:
        required_display = str(_parse_requirement_number(requirement) or requirement.value)
        return _build_comparison(
            field="Duolingo",
            requirement=required_display,
            applicant="Not uploaded",
            status=MatchStatus.FAIL,
            reason="Duolingo is required but no score was uploaded.",
            kind=_RuleKind.NUMERIC,
            knowledge_source=requirement.source,
        )

    if applicant_value is None and has_doc:
        required_display = str(_parse_requirement_number(requirement) or requirement.value)
        return _build_comparison(
            field="Duolingo",
            requirement=required_display,
            applicant="Uploaded (score not extracted)",
            status=MatchStatus.PARTIAL,
            reason="Duolingo score document uploaded but score could not be extracted.",
            kind=_RuleKind.NUMERIC,
            knowledge_source=requirement.source,
        )

    return _compare_numeric_threshold(
        field_label="Duolingo",
        requirement=requirement,
        applicant_numeric=applicant_value,
        applicant_display=str(applicant_value) if applicant_value is not None else overall,
        partial_tolerance=5.0,
        fail_action="Retake Duolingo English Test.",
        missing_applicant_reason="Duolingo score document uploaded but score could not be extracted.",
    )


def _compare_passport(
    profile: ApplicantProfile,
    documents: Sequence[Document],
    requirement: RetrievedRequirement | None,
) -> FieldComparison:
    uploaded = _has_uploaded_document(documents, "passport")
    applicant_label = "Uploaded" if uploaded else "Missing"

    passport = profile.passport
    if uploaded and passport:
        details = []
        if passport.full_name:
            details.append(f"name={passport.full_name}")
        if passport.expiry_date:
            details.append(f"expiry={passport.expiry_date}")
        if details:
            applicant_label = f"Uploaded ({', '.join(details)})"

    if requirement is None:
        return _build_comparison(
            field="Passport",
            requirement=None,
            applicant=applicant_label if uploaded else None,
            status=MatchStatus.UNKNOWN,
            reason="No passport requirement found in knowledge base.",
            kind=_RuleKind.DOCUMENT,
        )

    if not uploaded:
        return _build_comparison(
            field="Passport",
            requirement="Required",
            applicant="Missing",
            status=MatchStatus.FAIL,
            reason="Passport is required but no passport document was uploaded.",
            kind=_RuleKind.DOCUMENT,
            knowledge_source=requirement.source,
        )

    expiry = passport.expiry_date if passport else None
    parsed_expiry = _parse_expiry_date(expiry)

    if parsed_expiry and parsed_expiry < date.today():
        return _build_comparison(
            field="Passport",
            requirement="Required",
            applicant=applicant_label,
            status=MatchStatus.FAIL,
            reason=f"Passport is uploaded but expiry date ({expiry}) appears to be in the past.",
            kind=_RuleKind.DOCUMENT,
            knowledge_source=requirement.source,
        )

    if parsed_expiry and parsed_expiry <= date.today().replace(
        year=date.today().year + 1
    ):
        return _build_comparison(
            field="Passport",
            requirement="Required",
            applicant=applicant_label,
            status=MatchStatus.PARTIAL,
            reason=f"Passport is uploaded but expires within one year ({expiry}).",
            kind=_RuleKind.DOCUMENT,
            knowledge_source=requirement.source,
        )

    if not passport or not passport.full_name:
        return _build_comparison(
            field="Passport",
            requirement="Required",
            applicant=applicant_label,
            status=MatchStatus.PARTIAL,
            reason="Passport document uploaded but key identity fields were not extracted.",
            kind=_RuleKind.DOCUMENT,
            knowledge_source=requirement.source,
        )

    return _build_comparison(
        field="Passport",
        requirement="Required",
        applicant=applicant_label,
        status=MatchStatus.PASS,
        reason="Passport document uploaded with extracted identity details.",
        kind=_RuleKind.DOCUMENT,
        knowledge_source=requirement.source,
    )


def _compare_document_presence(
    *,
    field_label: str,
    document_type: str,
    documents: Sequence[Document],
    requirement: RetrievedRequirement | None,
    profile_detail: str | None = None,
    alternate_types: Sequence[str] = (),
    filename_keywords: Sequence[str] = (),
) -> FieldComparison:
    uploaded = _has_uploaded_document(
        documents,
        document_type,
        alternate_types=alternate_types,
    )
    if not uploaded and filename_keywords:
        uploaded = any(
            any(keyword in (document.file_name or "").lower() for keyword in filename_keywords)
            for document in documents
        )

    applicant_label = profile_detail or ("Uploaded" if uploaded else "Missing")

    if requirement is None:
        return _build_comparison(
            field=field_label,
            requirement=None,
            applicant=applicant_label if uploaded else None,
            status=MatchStatus.UNKNOWN,
            reason=f"No {field_label.lower()} requirement found in knowledge base.",
            kind=_RuleKind.DOCUMENT,
        )

    required_label = "Required"
    if uploaded:
        return _build_comparison(
            field=field_label,
            requirement=required_label,
            applicant=applicant_label,
            status=MatchStatus.PASS,
            reason=f"{field_label} requirement met — document uploaded.",
            kind=_RuleKind.DOCUMENT,
            knowledge_source=requirement.source,
        )

    return _build_comparison(
        field=field_label,
        requirement=required_label,
        applicant="Missing",
        status=MatchStatus.FAIL,
        reason=f"{field_label} is required but the document was not uploaded.",
        kind=_RuleKind.DOCUMENT,
        knowledge_source=requirement.source,
    )


def _compare_recommendation_letters(
    profile: ApplicantProfile,
    documents: Sequence[Document],
    requirement: RetrievedRequirement | None,
) -> FieldComparison:
    uploaded_count = sum(
        1 for document in documents if document.document_type == "letter_of_recommendation"
    )
    extracted_count = len(profile.recommendation_letters)
    count = max(uploaded_count, extracted_count)
    applicant_label = str(count)

    return _compare_count_requirement(
        field_label="Recommendation Letters",
        requirement=requirement,
        applicant_count=count,
        applicant_display=applicant_label,
        item_label="recommendation letter(s)",
    )


def _compare_application_deadline(
    requirement: RetrievedRequirement | None,
) -> FieldComparison:
    if requirement is None:
        return _build_comparison(
            field="Application Deadline",
            requirement=None,
            applicant=date.today().isoformat(),
            status=MatchStatus.UNKNOWN,
            reason="No application deadline found in knowledge base.",
            kind=_RuleKind.TEXT,
        )

    structured_values = _structured_text_values(requirement)
    deadline_raw = structured_values[0] if structured_values else requirement.value
    parsed = _parse_expiry_date(deadline_raw)
    if parsed is None:
        parsed = _parse_expiry_date(requirement.value)

    required_display = deadline_raw
    if parsed is not None:
        required_display = parsed.isoformat()

    today = date.today()
    applicant_display = today.isoformat()

    if parsed is None:
        return _build_comparison(
            field="Application Deadline",
            requirement=deadline_raw,
            applicant=applicant_display,
            status=MatchStatus.UNKNOWN,
            reason="Application deadline found but date could not be parsed.",
            kind=_RuleKind.TEXT,
            knowledge_source=requirement.source,
        )

    if today > parsed:
        status = MatchStatus.FAIL
        reason = f"Application deadline ({required_display}) has passed."
    elif today >= parsed - timedelta(days=7):
        status = MatchStatus.PARTIAL
        reason = f"Application deadline ({required_display}) is within one week."
    else:
        status = MatchStatus.PASS
        reason = f"Application deadline ({required_display}) has not passed."

    return _build_comparison(
        field="Application Deadline",
        requirement=required_display,
        applicant=applicant_display,
        status=status,
        reason=reason,
        kind=_RuleKind.TEXT,
        knowledge_source=requirement.source,
    )


def _compare_required_documents(
    documents: Sequence[Document],
    requirement: RetrievedRequirement | None,
) -> FieldComparison:
    if requirement is None:
        return _build_comparison(
            field="Required Documents",
            requirement=None,
            applicant=None,
            status=MatchStatus.UNKNOWN,
            reason="No required documents list found in knowledge base.",
            kind=_RuleKind.DOCUMENT,
        )

    doc_keys: list[str] = []
    if requirement.structured and isinstance(requirement.structured.value, list):
        doc_keys = [str(key) for key in requirement.structured.value]
    else:
        doc_keys = list(_REQUIRED_DOC_TYPE_MAP.keys())

    if not doc_keys:
        return _build_comparison(
            field="Required Documents",
            requirement=requirement.value,
            applicant=None,
            status=MatchStatus.UNKNOWN,
            reason="Required documents list could not be parsed.",
            kind=_RuleKind.DOCUMENT,
            knowledge_source=requirement.source,
        )

    present: list[str] = []
    missing: list[str] = []
    for doc_key in doc_keys:
        label = doc_key.replace("_", " ").title()
        if _document_uploaded(documents, doc_key):
            present.append(label)
        else:
            missing.append(label)

    applicant_label = f"{len(present)}/{len(doc_keys)} uploaded"
    required_label = ", ".join(doc_key.replace("_", " ") for doc_key in doc_keys)

    if not missing:
        status = MatchStatus.PASS
        reason = "All required documents are uploaded."
    elif not present:
        status = MatchStatus.FAIL
        reason = f"Missing required documents: {', '.join(missing)}."
    else:
        status = MatchStatus.PARTIAL
        reason = f"Partial document set uploaded. Missing: {', '.join(missing)}."

    return _build_comparison(
        field="Required Documents",
        requirement=required_label,
        applicant=applicant_label,
        status=status,
        reason=reason,
        kind=_RuleKind.DOCUMENT,
        knowledge_source=requirement.source,
    )


class RequirementMatchingEngine:
    """Retrieve KB requirements and compare them against an applicant profile."""

    def __init__(
        self,
        *,
        application_id: str,
        retriever: HybridRetriever | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.application_id = application_id
        self.settings = settings or get_settings()
        self.retriever = retriever or HybridRetriever(application_id=application_id)

    def _retrieve_requirement_context(self, base_query: str) -> list:
        from langchain_core.documents import Document

        seen_hashes: set[str] = set()
        merged: list[Document] = []

        queries = [base_query, *_FIELD_RETRIEVAL_QUERIES.values()]
        top_k = self.settings.retrieval_top_k

        for query in queries:
            for document in self.retriever.retrieve(query, k=top_k):
                content_key = document.page_content.strip()
                if not content_key or content_key in seen_hashes:
                    continue
                seen_hashes.add(content_key)
                merged.append(document)

        return merged

    def match(
        self,
        profile: ApplicantProfile,
        documents: Sequence[Document],
        *,
        retrieval_query: str,
        application_requirements: Sequence[Requirement] = (),
    ) -> RequirementMatchingResult:
        retrieved_docs = self._retrieve_requirement_context(retrieval_query)
        retrieved_requirements = extract_requirements_from_documents(retrieved_docs)
        req_map = _requirement_by_field(retrieved_requirements)

        sop_uploaded = _has_uploaded_document(
            documents,
            "statement_of_purpose",
            alternate_types=("motivation_letter",),
        )
        sop_detail = "Uploaded"
        if profile.sop and profile.sop.motivation:
            sop_detail = "Uploaded (motivation extracted)"
        elif not sop_uploaded:
            sop_detail = None

        cv_detail = None
        if profile.cv:
            cv_detail = f"Uploaded ({len(profile.cv.skills)} skills, {len(profile.cv.experience)} roles)"
        elif _has_uploaded_document(documents, "cv"):
            cv_detail = "Uploaded"

        transcript_detail = None
        if profile.transcript and profile.transcript.gpa:
            transcript_detail = f"Uploaded (GPA {profile.transcript.gpa})"
        elif _has_uploaded_document(documents, "academic_transcript"):
            transcript_detail = "Uploaded"

        comparisons: list[FieldComparison] = [
            _compare_gpa(profile, req_map.get("gpa")),
            _compare_degree(profile, req_map.get("degree")),
            _compare_major(profile, req_map.get("major")),
            _compare_nationality_or_country(
                field_label="Nationality",
                requirement=req_map.get("nationality"),
                applicant_value=_applicant_nationality(profile),
            ),
            _compare_nationality_or_country(
                field_label="Country Eligibility",
                requirement=req_map.get("country_eligibility"),
                applicant_value=_applicant_nationality(profile),
            ),
            _compare_english_requirement(profile, documents, req_map.get("english_requirement"), req_map),
            _compare_language_test(
                profile,
                documents,
                field_label="IELTS",
                requirement=req_map.get("ielts"),
                test_name="IELTS",
            ),
            _compare_language_test(
                profile,
                documents,
                field_label="TOEFL",
                requirement=req_map.get("toefl"),
                test_name="TOEFL",
            ),
            _compare_duolingo(profile, documents, req_map.get("duolingo")),
            _compare_passport(profile, documents, req_map.get("passport")),
            _compare_document_presence(
                field_label="Academic Transcript",
                document_type="academic_transcript",
                documents=documents,
                requirement=req_map.get("transcript"),
                profile_detail=transcript_detail,
            ),
            _compare_document_presence(
                field_label="Graduation Certificate",
                document_type="diploma",
                documents=documents,
                requirement=req_map.get("graduation_certificate"),
                profile_detail=(
                    "Uploaded"
                    if profile.degree_certificate
                    or _has_uploaded_document(documents, "diploma")
                    else None
                ),
            ),
            _compare_document_presence(
                field_label="CV / Resume",
                document_type="cv",
                documents=documents,
                requirement=req_map.get("cv"),
                profile_detail=cv_detail,
            ),
            _compare_document_presence(
                field_label="Statement of Purpose",
                document_type="statement_of_purpose",
                documents=documents,
                requirement=req_map.get("statement_of_purpose"),
                profile_detail=sop_detail,
                alternate_types=("motivation_letter",),
            ),
            _compare_document_presence(
                field_label="Motivation Letter",
                document_type="motivation_letter",
                documents=documents,
                requirement=req_map.get("motivation_letter"),
                profile_detail=sop_detail,
                alternate_types=("statement_of_purpose",),
            ),
            _compare_recommendation_letters(profile, documents, req_map.get("recommendation_letters")),
            _compare_work_experience(profile, documents, req_map.get("work_experience")),
            _compare_publications(profile, req_map.get("publications")),
            _compare_document_presence(
                field_label="Research Proposal",
                document_type="other",
                documents=documents,
                requirement=req_map.get("research_proposal"),
                filename_keywords=("research", "proposal"),
            ),
            _compare_document_presence(
                field_label="Financial Documents",
                document_type="other",
                documents=documents,
                requirement=req_map.get("financial_documents"),
                filename_keywords=("bank", "financial", "funds", "sponsor"),
            ),
            _compare_document_presence(
                field_label="Visa",
                document_type="other",
                documents=documents,
                requirement=req_map.get("visa"),
                filename_keywords=("visa",),
            ),
            _compare_required_documents(documents, req_map.get("required_documents")),
            _compare_application_deadline(req_map.get("application_deadline")),
        ]

        enriched = [_enrich_comparison(comparison) for comparison in comparisons]

        for app_requirement in application_requirements:
            extra = _compare_application_requirement(app_requirement, enriched)
            if extra:
                enriched.append(_enrich_comparison(extra))

        return RequirementMatchingResult(
            comparisons=enriched,
            retrieved_requirements=retrieved_requirements,
        )
