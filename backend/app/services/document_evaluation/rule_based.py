"""Deterministic, rule-based document evaluation helpers.

All objective checks live here — no LLM calls. Evaluators compose checks via
``RuleBasedScorer`` and return structured strengths, weaknesses, and suggestions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Callable

from app.schemas.document_evaluation import DocumentEvaluationLLMOutput

# ---------------------------------------------------------------------------
# Text pattern helpers
# ---------------------------------------------------------------------------

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}"
)
GITHUB_PATTERN = re.compile(r"github\.com/[\w.-]+", re.IGNORECASE)
LINKEDIN_PATTERN = re.compile(r"linkedin\.com/in/[\w.-]+", re.IGNORECASE)
GPA_PATTERN = re.compile(
    r"\b(?:gpa|cgpa|grade\s*point\s*average)\s*[:\s]?\s*(\d+\.?\d*)",
    re.IGNORECASE,
)
COURSE_LINE_PATTERN = re.compile(
    r"\b(?:course|subject|module)\b|\b[A-Z]{2,4}\s*\d{3,4}\b|\b\d{3,4}\s*[A-Z]{2,4}\b",
    re.IGNORECASE,
)
DATE_PATTERNS = (
    re.compile(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b"),
    re.compile(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b"),
    re.compile(
        r"\b(\d{1,2})\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|"
        r"May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
        r"Nov(?:ember)?|Dec(?:ember)?)\s+(\d{4})\b",
        re.IGNORECASE,
    ),
)
IELTS_EXPIRY_KEYWORDS = ("valid until", "validity", "test date", "date of test", "report date")
SIGNATURE_KEYWORDS = ("sincerely", "regards", "respectfully", "signature", "signed")
CLOSING_KEYWORDS = ("yours faithfully", "yours sincerely", "best regards", "kind regards")
OPENING_KEYWORDS = ("dear", "to whom it may concern", "admissions committee", "selection committee")
RELATIONSHIP_KEYWORDS = (
    "supervised",
    "taught",
    "mentored",
    "advised",
    "worked with",
    "known for",
    "professor",
    "supervisor",
    "manager",
    "colleague",
)
GENERIC_PHRASES = (
    "i have always dreamed",
    "since childhood",
    "prestigious university",
    "passion for excellence",
    "from a young age",
)
ATS_SECTIONS = ("experience", "education", "skills", "work history", "employment")
QUANTIFIED_MARKERS = ("%", "percent", "increased", "reduced", "saved", "grew", " users", " revenue")

MONTH_MAP = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}


def has_email(text: str) -> bool:
    return bool(EMAIL_PATTERN.search(text))


def has_phone(text: str) -> bool:
    return bool(PHONE_PATTERN.search(text))


def has_github(text: str) -> bool:
    return bool(GITHUB_PATTERN.search(text))


def has_linkedin(text: str) -> bool:
    return bool(LINKEDIN_PATTERN.search(text))


def has_section(text: str, *keywords: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def has_quantified_achievement(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in QUANTIFIED_MARKERS)


def word_count(text: str) -> int:
    return len(text.split())


def count_courses(text: str) -> int:
    """Heuristic count of course entries in transcript text."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    course_lines = sum(1 for line in lines if COURSE_LINE_PATTERN.search(line))
    if course_lines >= 3:
        return course_lines
    grade_markers = sum(
        1 for line in lines
        if re.search(r"\b[A-F][+-]?\b|\b\d\.\d+\b|\bpass\b|\bfail\b", line, re.IGNORECASE)
    )
    return max(course_lines, grade_markers // 2)


def parse_date(value: str) -> date | None:
    """Best-effort parse of a date string."""
    if not value:
        return None
    cleaned = value.strip()
    for pattern in DATE_PATTERNS:
        match = pattern.search(cleaned)
        if not match:
            continue
        groups = match.groups()
        try:
            if len(groups) == 3 and groups[1].isalpha() or groups[1].lower() in MONTH_MAP:
                day, month_str, year = groups
                month = MONTH_MAP.get(month_str.lower()[:3], MONTH_MAP.get(month_str.lower()))
                if month:
                    return date(int(year), month, int(day))
            elif int(groups[0]) > 31:
                return date(int(groups[0]), int(groups[1]), int(groups[2]))
            else:
                return date(int(groups[2]), int(groups[1]), int(groups[0]))
        except (ValueError, TypeError):
            continue
    year_match = re.search(r"\b(20\d{2}|19\d{2})\b", cleaned)
    if year_match:
        try:
            return date(int(year_match.group(1)), 12, 31)
        except ValueError:
            pass
    return None


def is_expired(expiry: date | None, *, reference: date | None = None) -> bool | None:
    """Return True if expired, False if valid, None if unknown."""
    if expiry is None:
        return None
    ref = reference or date.today()
    return expiry < ref


def ielts_validity_expired(text: str, *, reference: date | None = None) -> bool | None:
    """IELTS scores are typically valid for 2 years from test date."""
    lowered = text.lower()
    ref = reference or date.today()
    for pattern in DATE_PATTERNS:
        for match in pattern.finditer(text):
            parsed = parse_date(match.group(0))
            if parsed and parsed.year >= 2000:
                expiry = date(parsed.year + 2, parsed.month, parsed.day)
                return expiry < ref
    for keyword in IELTS_EXPIRY_KEYWORDS:
        idx = lowered.find(keyword)
        if idx >= 0:
            snippet = text[idx : idx + 60]
            parsed = parse_date(snippet)
            if parsed:
                expiry = date(parsed.year + 2, parsed.month, parsed.day)
                return expiry < ref
    return None


def has_opening_paragraph(text: str) -> bool:
    if not text.strip():
        return False
    first_block = text.strip().split("\n\n")[0] if "\n\n" in text else text.strip()[:500]
    lowered = first_block.lower()
    return any(kw in lowered for kw in OPENING_KEYWORDS) or word_count(first_block) >= 30


def has_closing_paragraph(text: str) -> bool:
    if not text.strip():
        return False
    last_block = text.strip().split("\n\n")[-1] if "\n\n" in text else text.strip()[-400:]
    lowered = last_block.lower()
    return any(kw in lowered for kw in CLOSING_KEYWORDS + SIGNATURE_KEYWORDS)


def has_personal_story_markers(text: str) -> bool:
    lowered = text.lower()
    markers = (
        "when i",
        "during my",
        "my experience",
        "i worked",
        "i led",
        "i developed",
        "growing up",
        "in my role",
        "this experience",
    )
    return sum(1 for m in markers if m in lowered) >= 2


def basic_grammar_heuristics(text: str) -> tuple[list[str], list[str], list[str]]:
    """Simple deterministic grammar/style checks (not LLM)."""
    strengths: list[str] = []
    weaknesses: list[str] = []
    suggestions: list[str] = []

    if not text.strip():
        return strengths, weaknesses, suggestions

    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) >= 5:
        strengths.append("Adequate sentence structure for review")
    else:
        weaknesses.append("Very few sentences detected")
        suggestions.append("Expand with complete sentences and paragraphs")

    long_sentences = sum(1 for s in sentences if len(s.split()) > 40)
    if long_sentences > 2:
        weaknesses.append("Several overly long sentences detected")
        suggestions.append("Break long sentences into shorter, clearer statements")

    repeated = re.findall(r"\b(\w{4,})\b", text.lower())
    from collections import Counter
    counts = Counter(repeated)
    overused = [w for w, c in counts.items() if c > 8 and w not in {"that", "this", "with", "from", "have", "will", "would", "their", "about"}]
    if overused:
        weaknesses.append(f"Repeated word usage detected: {', '.join(overused[:3])}")
        suggestions.append("Vary vocabulary to avoid repetitive phrasing")

    if not weaknesses and sentences:
        strengths.append("No obvious grammar issues detected by automated checks")

    return strengths, weaknesses, suggestions


# ---------------------------------------------------------------------------
# Scoring framework
# ---------------------------------------------------------------------------

@dataclass
class EvaluationCheck:
    """Single deterministic check with weighted pass/fail outcome."""

    name: str
    passed: bool
    weight: int = 10
    strength: str | None = None
    weakness: str | None = None
    suggestion: str | None = None
    missing_info: str | None = None


@dataclass
class RuleBasedScorer:
    """Accumulates weighted checks and builds a ``DocumentEvaluationLLMOutput``."""

    checks: list[EvaluationCheck] = field(default_factory=list)
    base_score: int = 0
    max_score: int = 100
    confidence: float = 0.95

    def add(
        self,
        name: str,
        passed: bool,
        *,
        weight: int = 10,
        strength: str | None = None,
        weakness: str | None = None,
        suggestion: str | None = None,
        missing_info: str | None = None,
    ) -> RuleBasedScorer:
        self.checks.append(
            EvaluationCheck(
                name=name,
                passed=passed,
                weight=weight,
                strength=strength,
                weakness=weakness,
                suggestion=suggestion,
                missing_info=missing_info,
            )
        )
        return self

    def add_if(
        self,
        name: str,
        condition: bool,
        *,
        weight: int = 10,
        strength: str,
        weakness: str,
        suggestion: str | None = None,
        missing_info: str | None = None,
    ) -> RuleBasedScorer:
        return self.add(
            name,
            condition,
            weight=weight,
            strength=strength if condition else None,
            weakness=weakness if not condition else None,
            suggestion=suggestion if not condition else None,
            missing_info=missing_info if not condition else None,
        )

    def add_field(
        self,
        name: str,
        value: object,
        *,
        weight: int = 10,
        strength: str,
        weakness: str,
        suggestion: str | None = None,
    ) -> RuleBasedScorer:
        passed = bool(value) and value not in ([], {}, "")
        return self.add_if(
            name,
            passed,
            weight=weight,
            strength=strength,
            weakness=weakness,
            suggestion=suggestion,
            missing_info=weakness if not passed else None,
        )

    def total_weight(self) -> int:
        return sum(c.weight for c in self.checks) or 1

    def earned_weight(self) -> int:
        return sum(c.weight for c in self.checks if c.passed)

    def compute_score(self) -> int:
        if not self.checks:
            return 0
        ratio = self.earned_weight() / self.total_weight()
        raw = self.base_score + int(ratio * (self.max_score - self.base_score))
        return max(0, min(self.max_score, raw))

    def build(self) -> DocumentEvaluationLLMOutput:
        strengths = [c.strength for c in self.checks if c.passed and c.strength]
        weaknesses = [c.weakness for c in self.checks if not c.passed and c.weakness]
        suggestions = [c.suggestion for c in self.checks if not c.passed and c.suggestion]
        missing = [c.missing_info for c in self.checks if not c.passed and c.missing_info]

        # Deduplicate while preserving order
        def _dedupe(items: list[str | None]) -> list[str]:
            seen: set[str] = set()
            result: list[str] = []
            for item in items:
                if not item:
                    continue
                key = item.lower()
                if key in seen:
                    continue
                seen.add(key)
                result.append(item)
            return result

        return DocumentEvaluationLLMOutput(
            quality_score=self.compute_score(),
            strengths=_dedupe(strengths),
            weaknesses=_dedupe(weaknesses),
            missing_information=_dedupe(missing),
            suggestions=_dedupe(suggestions),
            confidence=self.confidence,
        )


def merge_grammar_feedback(
    output: DocumentEvaluationLLMOutput,
    text: str,
) -> DocumentEvaluationLLMOutput:
    """Append deterministic grammar/style feedback to an evaluation output."""
    if not text.strip():
        return output

    g_strengths, g_weaknesses, g_suggestions = basic_grammar_heuristics(text)

    def _dedupe(items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(item)
        return result

    return DocumentEvaluationLLMOutput(
        quality_score=output.quality_score,
        strengths=_dedupe(output.strengths + g_strengths),
        weaknesses=_dedupe(output.weaknesses + g_weaknesses),
        missing_information=output.missing_information,
        suggestions=_dedupe(output.suggestions + g_suggestions),
        confidence=output.confidence,
    )


def merge_evaluations(
    objective: DocumentEvaluationLLMOutput,
    subjective: DocumentEvaluationLLMOutput | None,
    *,
    objective_weight: float = 0.7,
) -> DocumentEvaluationLLMOutput:
    """Combine rule-based objective results with optional subjective LLM writing assessment."""
    if subjective is None:
        return objective

    subj_weight = 1.0 - objective_weight
    combined_score = int(
        objective_weight * objective.quality_score + subj_weight * subjective.quality_score
    )
    combined_score = max(0, min(100, combined_score))

    def _dedupe(items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            result.append(item)
        return result

    return DocumentEvaluationLLMOutput(
        quality_score=combined_score,
        strengths=_dedupe(objective.strengths + subjective.strengths),
        weaknesses=_dedupe(objective.weaknesses + subjective.weaknesses),
        missing_information=_dedupe(objective.missing_information + subjective.missing_information),
        suggestions=_dedupe(objective.suggestions + subjective.suggestions),
        confidence=min(objective.confidence, subjective.confidence),
    )
