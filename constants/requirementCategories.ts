/** Requirement categories stored in Supabase `requirements.category`. */
export enum RequirementCategory {
  Eligibility = 'eligibility',
  Documents = 'documents',
  Language = 'language',
  Academic = 'academic',
  Financial = 'financial',
  Recommendation = 'recommendation',
  Identity = 'identity',
  Deadline = 'deadline',
  Other = 'other',
}

/** Human-readable labels for requirement categories. */
export const REQUIREMENT_CATEGORY_LABELS: Record<RequirementCategory, string> = {
  [RequirementCategory.Eligibility]: 'Eligibility',
  [RequirementCategory.Documents]: 'Required Documents',
  [RequirementCategory.Language]: 'Language Requirements',
  [RequirementCategory.Academic]: 'Academic Requirements',
  [RequirementCategory.Financial]: 'Financial Requirements',
  [RequirementCategory.Recommendation]: 'Recommendation Letters',
  [RequirementCategory.Identity]: 'Identity & Passport',
  [RequirementCategory.Deadline]: 'Deadlines',
  [RequirementCategory.Other]: 'Other',
};

/** Priority levels for missing requirements in analysis output. */
export enum RequirementPriority {
  High = 'high',
  Medium = 'medium',
  Low = 'low',
}

/** All requirement categories as an array. */
export const REQUIREMENT_CATEGORIES = Object.values(RequirementCategory);

/** All requirement priority levels as an array. */
export const REQUIREMENT_PRIORITIES = Object.values(RequirementPriority);

export type { RequirementCategory as RequirementCategoryType };
export type { RequirementPriority as RequirementPriorityType };
