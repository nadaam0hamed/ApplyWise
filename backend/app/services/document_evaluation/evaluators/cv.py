"""CV / Resume quality evaluator."""

from __future__ import annotations

from app.chains.extraction_parser import ApplicantProfile, ExtractedDocument
from app.models import Document, Requirement
from app.schemas.document_evaluation import DocumentEvaluationLLMOutput
from app.services.document_evaluation.evaluators.base import BaseDocumentEvaluator
from app.services.document_evaluation.rule_based import (
    ATS_SECTIONS,
    RuleBasedScorer,
    has_email,
    has_github,
    has_linkedin,
    has_phone,
    has_quantified_achievement,
    has_section,
    word_count,
)


class CVEvaluator(BaseDocumentEvaluator):
    supported_types = ("cv",)

    def evaluation_criteria(self) -> str:
        return (
            "- Contact information (email, phone)\n"
            "- Education\n"
            "- Work experience with measurable impact\n"
            "- Technical and soft skills\n"
            "- Projects and leadership activities\n"
            "- Formatting and ATS compatibility\n"
            "- Professional links (GitHub, LinkedIn)"
        )

    def uses_subjective_llm(self) -> bool:
        return True

    def subjective_criteria(self) -> str:
        return (
            "- Professional summary and bullet-point clarity\n"
            "- Concise, impactful phrasing in experience descriptions\n"
            "- Overall readability and professional tone"
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
        cv = extracted.cv if extracted else (applicant_profile.cv if applicant_profile else None)
        text = document_text or ""

        if not (text or cv):
            return DocumentEvaluationLLMOutput(
                quality_score=0,
                weaknesses=["CV content unavailable for evaluation"],
                suggestions=["Upload a readable PDF or DOCX CV"],
            )

        scorer = RuleBasedScorer()

        # Contact information
        scorer.add_if(
            "contact_email",
            has_email(text),
            weight=8,
            strength="Contact email present",
            weakness="No contact email detected",
            suggestion="Add a professional email address in the header",
        )
        scorer.add_if(
            "contact_phone",
            has_phone(text),
            weight=6,
            strength="Contact phone number present",
            weakness="No phone number detected",
            suggestion="Include a reachable phone number",
        )

        # Education
        education_found = has_section(text, "education", "bachelor", "master", "university", "degree")
        scorer.add_if(
            "education",
            education_found,
            weight=10,
            strength="Education section present",
            weakness="No education section detected",
            suggestion="Add an education section with degree, institution, and dates",
        )

        # Extracted structured fields
        scorer.add_field(
            "skills",
            cv.skills if cv else [],
            weight=10,
            strength="Relevant skills section present",
            weakness="No skills section detected",
            suggestion="Add a dedicated skills section with role-relevant competencies",
        )
        scorer.add_field(
            "experience",
            cv.experience if cv else [],
            weight=12,
            strength="Work experience included",
            weakness="No work experience listed",
            suggestion="Add internships, part-time roles, or research assistantships",
        )
        scorer.add_field(
            "projects",
            cv.projects if cv else [],
            weight=8,
            strength="Projects section strengthens technical credibility",
            weakness="No projects section detected",
            suggestion="Include 2-3 projects with technologies used and outcomes",
        )
        scorer.add_field(
            "leadership",
            cv.leadership if cv else [],
            weight=8,
            strength="Leadership activities highlighted",
            weakness="No leadership activities listed",
            suggestion="Highlight club, team, or community leadership roles",
        )

        # Formatting & ATS friendliness
        ats_sections_found = sum(1 for section in ATS_SECTIONS if section in text.lower())
        scorer.add_if(
            "ats_sections",
            ats_sections_found >= 2,
            weight=8,
            strength="Standard CV sections detected (ATS friendly)",
            weakness="Missing standard CV section headings",
            suggestion="Use clear headings: Experience, Education, Skills",
        )
        scorer.add_if(
            "formatting_length",
            50 <= word_count(text) <= 800,
            weight=6,
            strength="Appropriate CV length",
            weakness="CV may be too short or too long for early-career applications",
            suggestion="Keep the CV to one page unless you have 8+ years of experience",
        )

        # GitHub & LinkedIn
        scorer.add_if(
            "github",
            has_github(text),
            weight=6,
            strength="GitHub profile link included",
            weakness="No GitHub profile link detected",
            suggestion="Add your GitHub profile URL for technical roles",
        )
        scorer.add_if(
            "linkedin",
            has_linkedin(text),
            weight=6,
            strength="LinkedIn profile link included",
            weakness="No LinkedIn profile link detected",
            suggestion="Add your LinkedIn profile URL",
        )

        # Quantified achievements
        scorer.add_if(
            "quantified_achievements",
            has_quantified_achievement(text),
            weight=8,
            strength="Quantified achievements present",
            weakness="No quantified achievements detected",
            suggestion="Add measurable impact (e.g., 'Improved performance by 30%')",
        )

        if not cv and text:
            scorer.add(
                "structured_parse",
                False,
                weight=5,
                weakness="Structured CV content could not be parsed",
                suggestion="Use a standard CV layout with clearly labeled sections",
            )

        return scorer.build()
