"""IELTS / TOEFL language certificate quality evaluator."""

from __future__ import annotations

from app.chains.extraction_parser import ApplicantProfile, ExtractedDocument
from app.models import Document, Requirement
from app.schemas.document_evaluation import DocumentEvaluationLLMOutput
from app.services.document_evaluation.evaluators.base import BaseDocumentEvaluator
from app.services.document_evaluation.rule_based import (
    RuleBasedScorer,
    ielts_validity_expired,
    word_count,
)


class LanguageCertificateEvaluator(BaseDocumentEvaluator):
    supported_types = ("ielts_score", "toefl_score", "gre_score")

    def evaluation_criteria(self) -> str:
        return (
            "- Test type clearly identified\n"
            "- Overall score visible\n"
            "- All component/section scores present\n"
            "- Test date and validity (IELTS: 2-year rule)\n"
            "- Candidate name and report number legible"
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
        language = extracted.language_test if extracted else (
            applicant_profile.language_test if applicant_profile else None
        )
        text = document_text or ""
        doc_type = document.document_type or ""
        scorer = RuleBasedScorer()

        # Test type
        scorer.add_field(
            "test_type",
            language.test_type if language else None,
            weight=10,
            strength="Test type identified",
            weakness="Test type not detected",
            suggestion="Upload the complete official score report showing test name",
        )

        # Overall score
        scorer.add_field(
            "overall_score",
            language.overall_score if language else None,
            weight=25,
            strength="Overall score extracted",
            weakness="Overall score not detected",
            suggestion="Upload the complete official score report with overall band/score",
        )

        # Component scores
        section_fields = ["reading", "listening", "writing", "speaking"]
        populated_sections = sum(
            1 for field in section_fields if language and getattr(language, field)
        )
        scorer.add_if(
            "component_scores",
            populated_sections >= 3,
            weight=25,
            strength=f"Individual section scores present ({populated_sections}/4)",
            weakness="Incomplete section scores",
            suggestion="Ensure all four section scores are visible on the report",
        )

        # IELTS expiry (2-year validity rule)
        if doc_type == "ielts_score" or (language and (language.test_type or "").lower().startswith("ielts")):
            expired = ielts_validity_expired(text)
            if expired is True:
                scorer.add(
                    "ielts_validity",
                    False,
                    weight=20,
                    weakness="IELTS score may be expired (valid for 2 years)",
                    suggestion="Retake IELTS or upload a score report within the 2-year validity window",
                )
            elif expired is False:
                scorer.add(
                    "ielts_validity",
                    True,
                    weight=20,
                    strength="IELTS score appears within validity period",
                )
            else:
                scorer.add(
                    "ielts_validity",
                    False,
                    weight=10,
                    weakness="IELTS test date not detected for validity check",
                    suggestion="Ensure the test date is clearly visible on the score report",
                )
        else:
            # Non-IELTS: check that a date is present in the document
            has_date = any(kw in text.lower() for kw in ("test date", "date of test", "report date", "20"))
            scorer.add_if(
                "test_date",
                has_date,
                weight=15,
                strength="Test date information present",
                weakness="Test date not clearly visible",
                suggestion="Ensure the test date is legible on the score report",
            )

        # Readability
        scorer.add_if(
            "readability",
            word_count(text) >= 30 or bool(language and language.overall_score),
            weight=10,
            strength="Score report content is readable",
            weakness="Score report may be incomplete or unreadable",
            suggestion="Upload an official PDF score report, not a partial screenshot",
        )

        if not language and not text:
            return DocumentEvaluationLLMOutput(
                quality_score=0,
                weaknesses=["Language test data could not be extracted"],
                suggestions=["Upload an official IELTS/TOEFL score report PDF"],
            )

        return scorer.build()
