"""Passport / identity document quality evaluator."""

from __future__ import annotations

from app.chains.extraction_parser import ApplicantProfile, ExtractedDocument
from app.models import Document, Requirement
from app.schemas.document_evaluation import DocumentEvaluationLLMOutput
from app.services.document_evaluation.evaluators.base import BaseDocumentEvaluator
from app.services.document_evaluation.rule_based import (
    RuleBasedScorer,
    is_expired,
    parse_date,
    word_count,
)


class PassportEvaluator(BaseDocumentEvaluator):
    supported_types = ("passport",)

    def evaluation_criteria(self) -> str:
        return (
            "- Full name clearly readable\n"
            "- Passport number legible\n"
            "- Expiry date present and valid\n"
            "- Nationality identified\n"
            "- Document readability (no blur or cropping)"
        )

    def evaluate_rule_based(
        self,
        *,
        document: Document,
        extracted: ExtractedDocument | None,
        applicant_profile: ApplicantProfile | None,
        requirements: list[Requirement],
        document_text: str | None,
    ) -> DocumentEvaluationLLMOutput:
        passport = extracted.passport if extracted else (
            applicant_profile.passport if applicant_profile else None
        )
        text = document_text or ""
        scorer = RuleBasedScorer()

        # Full name
        scorer.add_field(
            "full_name",
            passport.full_name if passport else None,
            weight=20,
            strength="Full name extracted",
            weakness="Full name not readable",
            suggestion="Ensure the biographical page shows your full name clearly",
        )

        # Passport number
        scorer.add_field(
            "passport_number",
            passport.passport_number if passport else None,
            weight=20,
            strength="Passport number present",
            weakness="Passport number missing or illegible",
            suggestion="Upload a scan where the passport number is clearly visible",
        )

        # Expiry date
        expiry_raw = passport.expiry_date if passport else None
        expiry_date = parse_date(expiry_raw or "")
        scorer.add_field(
            "expiry_date",
            expiry_raw,
            weight=20,
            strength="Expiry date present",
            weakness="Expiry date not found",
            suggestion="Ensure the passport expiry date page is clearly visible",
        )

        expired = is_expired(expiry_date)
        if expiry_date is not None:
            scorer.add_if(
                "expiry_valid",
                expired is False,
                weight=20,
                strength="Passport is not expired",
                weakness="Passport appears to be expired",
                suggestion="Renew your passport before submitting the application",
            )
        elif expiry_raw:
            scorer.add(
                "expiry_valid",
                False,
                weight=10,
                weakness="Expiry date could not be parsed",
                suggestion="Ensure the expiry date is clearly readable",
            )

        # Nationality
        scorer.add_field(
            "nationality",
            passport.nationality if passport else None,
            weight=10,
            strength="Nationality identified",
            weakness="Nationality not detected",
            suggestion="Ensure nationality/citizenship field is visible on the scan",
        )

        # Readability — enough text extracted to evaluate
        readable = word_count(text) >= 20 or bool(passport and passport.full_name)
        scorer.add_if(
            "readability",
            readable,
            weight=10,
            strength="Passport content is readable",
            weakness="Passport scan may be blurry, cropped, or unreadable",
            suggestion="Upload a high-resolution scan of the biographical page",
        )

        if not passport and not text:
            return DocumentEvaluationLLMOutput(
                quality_score=0,
                weaknesses=["Passport content unavailable for evaluation"],
                suggestions=["Upload a high-resolution scan of the biographical page"],
            )

        return scorer.build()
