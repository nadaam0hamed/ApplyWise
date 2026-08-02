import type { RequirementCategory } from '@/constants/requirementCategories';

/**
 * Maps to the live `requirements` Supabase table.
 * Columns: id, application_id, category, created_at
 */
export interface Requirement {
  id: string;
  application_id: string;
  category: RequirementCategory;
  created_at: string;
  /** Derived from category label when not stored in DB. */
  title?: string;
  description?: string | null;
  is_required?: boolean;
  is_fulfilled?: boolean;
  eligibility?: string | null;
  language_requirement?: string | null;
  gpa_requirement?: string | null;
  recommendation_letters_count?: number | null;
  passport_requirement?: string | null;
  source_url?: string | null;
  extracted_data?: ExtractedRequirementsData | null;
  sort_order?: number;
  updated_at?: string;
}

/** Maps to the live `requirement_status` Supabase table. */
export interface RequirementStatus {
  id: string;
  requirement_id: string;
  status: RequirementStatusValue;
  created_at: string;
}

export type RequirementStatusValue = 'fulfilled' | 'missing' | 'pending';

/** Structured data extracted from URL/PDF requirement sources. */
export interface ExtractedRequirementsData {
  scholarship_name: string;
  country: string;
  deadline: string;
  eligibility: string;
  required_documents: string[];
  language_requirement: string;
  gpa_requirement: string;
  recommendation_letters: number;
  passport_requirement: string;
}

/** Payload for creating a requirement record. */
export interface RequirementInsert {
  application_id: string;
  category: RequirementCategory;
  created_at?: string;
}

/** Payload for updating requirement fulfillment status. */
export type RequirementUpdate = Partial<
  Omit<Requirement, 'id' | 'application_id' | 'created_at'>
>;

/** Checklist item derived from requirements for UI display. */
export interface RequirementChecklistItem {
  id: string;
  title: string;
  is_required: boolean;
  is_fulfilled: boolean;
  category: RequirementCategory;
}
