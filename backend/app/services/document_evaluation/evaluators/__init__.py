"""Type-specific document quality evaluators."""

from app.services.document_evaluation.evaluators.base import BaseDocumentEvaluator
from app.services.document_evaluation.evaluators.cv import CVEvaluator
from app.services.document_evaluation.evaluators.financial import FinancialDocumentsEvaluator
from app.services.document_evaluation.evaluators.generic import GenericDocumentEvaluator
from app.services.document_evaluation.evaluators.graduation_certificate import GraduationCertificateEvaluator
from app.services.document_evaluation.evaluators.language_certificate import LanguageCertificateEvaluator
from app.services.document_evaluation.evaluators.motivation import MotivationLetterEvaluator
from app.services.document_evaluation.evaluators.passport import PassportEvaluator
from app.services.document_evaluation.evaluators.recommendation import RecommendationLetterEvaluator
from app.services.document_evaluation.evaluators.research_proposal import ResearchProposalEvaluator
from app.services.document_evaluation.evaluators.sop import SOPEvaluator
from app.services.document_evaluation.evaluators.transcript import TranscriptEvaluator

__all__ = [
    "BaseDocumentEvaluator",
    "CVEvaluator",
    "FinancialDocumentsEvaluator",
    "GenericDocumentEvaluator",
    "GraduationCertificateEvaluator",
    "LanguageCertificateEvaluator",
    "MotivationLetterEvaluator",
    "PassportEvaluator",
    "RecommendationLetterEvaluator",
    "ResearchProposalEvaluator",
    "SOPEvaluator",
    "TranscriptEvaluator",
]
