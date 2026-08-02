/** Document processing statuses used in UI and analysis flows (not stored on `documents`). */
export enum DocumentStatus {
  Uploaded = 'uploaded',
  Processing = 'processing',
  Complete = 'complete',
  Error = 'error',
}

/** Canonical document types for scholarship/admission applications. */
export enum DocumentType {
  Passport = 'passport',
  Cv = 'cv',
  AcademicTranscript = 'academic_transcript',
  MotivationLetter = 'motivation_letter',
  StatementOfPurpose = 'statement_of_purpose',
  LetterOfRecommendation = 'letter_of_recommendation',
  IeltsScore = 'ielts_score',
  ToeflScore = 'toefl_score',
  GreScore = 'gre_score',
  Diploma = 'diploma',
  ApplicationForm = 'application_form',
  Other = 'other',
}

/** Human-readable labels for document types. */
export const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  [DocumentType.Passport]: 'Passport',
  [DocumentType.Cv]: 'CV / Resume',
  [DocumentType.AcademicTranscript]: 'Academic Transcript',
  [DocumentType.MotivationLetter]: 'Motivation Letter',
  [DocumentType.StatementOfPurpose]: 'Statement of Purpose',
  [DocumentType.LetterOfRecommendation]: 'Letter of Recommendation',
  [DocumentType.IeltsScore]: 'IELTS Score',
  [DocumentType.ToeflScore]: 'TOEFL Score',
  [DocumentType.GreScore]: 'GRE Score',
  [DocumentType.Diploma]: 'Diploma / Degree Certificate',
  [DocumentType.ApplicationForm]: 'Application Form',
  [DocumentType.Other]: 'Other',
};

/** MIME types accepted for document upload. */
export const SUPPORTED_MIME_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'image/png',
  'image/jpeg',
] as const;

/** File extensions accepted for document upload. */
export const SUPPORTED_FILE_EXTENSIONS = ['pdf', 'docx', 'png', 'jpg', 'jpeg'] as const;

/** Required document slots shown on the application details page. */
export type ApplicationDocumentSlot = {
  key: string;
  label: string;
  documentTypes: DocumentType[];
  defaultDocumentType: DocumentType;
};

export const APPLICATION_DOCUMENT_SLOTS: ApplicationDocumentSlot[] = [
  {
    key: 'cv',
    label: 'CV',
    documentTypes: [DocumentType.Cv],
    defaultDocumentType: DocumentType.Cv,
  },
  {
    key: 'passport',
    label: 'Passport',
    documentTypes: [DocumentType.Passport],
    defaultDocumentType: DocumentType.Passport,
  },
  {
    key: 'transcript',
    label: 'Academic Transcript',
    documentTypes: [DocumentType.AcademicTranscript],
    defaultDocumentType: DocumentType.AcademicTranscript,
  },
  {
    key: 'language',
    label: 'IELTS/TOEFL',
    documentTypes: [DocumentType.IeltsScore, DocumentType.ToeflScore],
    defaultDocumentType: DocumentType.IeltsScore,
  },
  {
    key: 'recommendation',
    label: 'Recommendation Letter',
    documentTypes: [DocumentType.LetterOfRecommendation],
    defaultDocumentType: DocumentType.LetterOfRecommendation,
  },
  {
    key: 'sop',
    label: 'Statement of Purpose',
    documentTypes: [DocumentType.StatementOfPurpose],
    defaultDocumentType: DocumentType.StatementOfPurpose,
  },
];

/** All document types as an array. */
export const DOCUMENT_TYPES = Object.values(DocumentType);

/** All document statuses as an array. */
export const DOCUMENT_STATUSES = Object.values(DocumentStatus);

export type SupportedMimeType = (typeof SUPPORTED_MIME_TYPES)[number];
export type SupportedFileExtension = (typeof SUPPORTED_FILE_EXTENSIONS)[number];
