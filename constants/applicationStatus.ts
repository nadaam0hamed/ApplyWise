/** Application lifecycle statuses stored in Supabase `applications.status`. */
export enum ApplicationStatus {
  Draft = 'draft',
  InProgress = 'in_progress',
  Analyzing = 'analyzing',
  Ready = 'ready',
  Submitted = 'submitted',
  Accepted = 'accepted',
  Rejected = 'rejected',
}

/** Types of applications supported by ApplyWise. */
export enum ApplicationType {
  Scholarship = 'scholarship',
  University = 'university',
  Visa = 'visa',
  Passport = 'passport',
  Residency = 'residency',
}

/** How requirement data was provided for an application. */
export enum RequirementSource {
  Program = 'program',
  Url = 'url',
  Pdf = 'pdf',
  Manual = 'manual',
}

/** Human-readable labels for application statuses. */
export const APPLICATION_STATUS_LABELS: Record<ApplicationStatus, string> = {
  [ApplicationStatus.Draft]: 'Draft',
  [ApplicationStatus.InProgress]: 'In Progress',
  [ApplicationStatus.Analyzing]: 'Analyzing',
  [ApplicationStatus.Ready]: 'Ready to Submit',
  [ApplicationStatus.Submitted]: 'Submitted',
  [ApplicationStatus.Accepted]: 'Accepted',
  [ApplicationStatus.Rejected]: 'Rejected',
};

/** All application statuses as an array for select/filter UI. */
export const APPLICATION_STATUSES = Object.values(ApplicationStatus);

/** Human-readable labels for application types. */
export const APPLICATION_TYPE_LABELS: Record<ApplicationType, string> = {
  [ApplicationType.Scholarship]: 'Scholarship',
  [ApplicationType.University]: 'University Admission',
  [ApplicationType.Visa]: 'Student Visa',
  [ApplicationType.Passport]: 'Passport',
  [ApplicationType.Residency]: 'Residency Permit',
};

/** Icons for application types in onboarding UI. */
export const APPLICATION_TYPE_ICONS: Record<ApplicationType, string> = {
  [ApplicationType.Scholarship]: '🎓',
  [ApplicationType.University]: '🏫',
  [ApplicationType.Visa]: '✈️',
  [ApplicationType.Passport]: '📘',
  [ApplicationType.Residency]: '🏠',
};

/** All application types as an array for onboarding UI. */
export const APPLICATION_TYPES = Object.values(ApplicationType);

/** All requirement source options. */
export const REQUIREMENT_SOURCES = Object.values(RequirementSource);

export type { ApplicationStatus as ApplicationStatusType };
export type { ApplicationType as ApplicationTypeValue };
export type { RequirementSource as RequirementSourceType };
