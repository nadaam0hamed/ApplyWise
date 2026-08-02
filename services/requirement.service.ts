import { requireUserId } from '@/lib/auth-helpers';
import {
  REQUIREMENT_COLUMNS,
  REQUIREMENT_STATUS_COLUMNS,
} from '@/lib/supabase-live-schema';
import { supabase } from '@/lib/supabase';
import { DocumentType } from '@/constants/documentTypes';
import {
  REQUIREMENT_CATEGORY_LABELS,
  RequirementCategory,
} from '@/constants/requirementCategories';
import type { Document } from '@/types/document';
import type { Requirement, RequirementStatusValue } from '@/types/requirement';
import type { ExtractedRequirementsData } from '@/types/requirement';

const REQUIRED_CATEGORIES = new Set<RequirementCategory>([
  RequirementCategory.Eligibility,
  RequirementCategory.Documents,
  RequirementCategory.Language,
  RequirementCategory.Academic,
  RequirementCategory.Recommendation,
  RequirementCategory.Identity,
]);

function hasDocumentForTypes(documents: Document[], types: DocumentType[]): boolean {
  return documents.some((doc) => doc.document_type && types.includes(doc.document_type));
}

/** Derives fulfillment from uploaded documents and requirement category. */
export function evaluateRequirementFulfillment(
  category: RequirementCategory,
  documents: Document[],
): boolean {
  switch (category) {
    case RequirementCategory.Documents:
      return documents.length > 0;
    case RequirementCategory.Language:
      return hasDocumentForTypes(documents, [DocumentType.IeltsScore, DocumentType.ToeflScore]);
    case RequirementCategory.Academic:
      return hasDocumentForTypes(documents, [DocumentType.AcademicTranscript]);
    case RequirementCategory.Recommendation:
      return hasDocumentForTypes(documents, [DocumentType.LetterOfRecommendation]);
    case RequirementCategory.Identity:
      return hasDocumentForTypes(documents, [DocumentType.Passport]);
    case RequirementCategory.Eligibility:
      return hasDocumentForTypes(documents, [DocumentType.Cv, DocumentType.AcademicTranscript]);
    case RequirementCategory.Financial:
      return hasDocumentForTypes(documents, [DocumentType.Other]);
    case RequirementCategory.Deadline:
      return true;
    default:
      return false;
  }
}

function enrichRequirement(
  row: Pick<Requirement, 'id' | 'application_id' | 'category' | 'created_at'>,
  status: RequirementStatusValue | null,
): Requirement {
  const category = row.category as RequirementCategory;

  return {
    ...row,
    category,
    title: REQUIREMENT_CATEGORY_LABELS[category] ?? category,
    is_required: REQUIRED_CATEGORIES.has(category),
    is_fulfilled: status === 'fulfilled',
    description: null,
    eligibility: null,
    language_requirement: null,
    gpa_requirement: null,
    recommendation_letters_count: null,
    passport_requirement: null,
    source_url: null,
    extracted_data: null,
  };
}

async function loadStatuses(requirementIds: string[]): Promise<Map<string, RequirementStatusValue>> {
  if (requirementIds.length === 0) return new Map();

  const { data, error } = await supabase
    .from('requirement_status')
    .select(REQUIREMENT_STATUS_COLUMNS)
    .in('requirement_id', requirementIds);

  if (error) throw new Error(error.message);

  return new Map(
    (data ?? []).map((row) => [row.requirement_id, row.status as RequirementStatusValue]),
  );
}

export const RequirementService = {
  async listByApplication(applicationId: string): Promise<Requirement[]> {
    const { data, error } = await supabase
      .from('requirements')
      .select(REQUIREMENT_COLUMNS)
      .eq('application_id', applicationId)
      .order('created_at', { ascending: true });

    if (error) throw new Error(error.message);

    const rows = data ?? [];
    const statusMap = await loadStatuses(rows.map((row) => row.id));

    return rows.map((row) =>
      enrichRequirement(row as Requirement, statusMap.get(row.id) ?? null),
    );
  },

  async createFromExtractedData(
    applicationId: string,
    data: ExtractedRequirementsData,
  ): Promise<Requirement[]> {
    await requireUserId();
    const now = new Date().toISOString();

    const categories = [
      RequirementCategory.Eligibility,
      RequirementCategory.Language,
      RequirementCategory.Academic,
      RequirementCategory.Recommendation,
      RequirementCategory.Identity,
      ...data.required_documents.map(() => RequirementCategory.Documents),
    ];

    const { data: inserted, error } = await supabase
      .from('requirements')
      .insert(
        categories.map((category) => ({
          application_id: applicationId,
          category,
          created_at: now,
        })),
      )
      .select(REQUIREMENT_COLUMNS);

    if (error) throw new Error(error.message);

    return (inserted ?? []).map((row) => enrichRequirement(row as Requirement, 'missing'));
  },


  async createDefaultCategories(applicationId: string): Promise<Requirement[]> {
    await requireUserId();
    const now = new Date().toISOString();

    const categories = [
      RequirementCategory.Eligibility,
      RequirementCategory.Documents,
      RequirementCategory.Language,
      RequirementCategory.Academic,
      RequirementCategory.Recommendation,
      RequirementCategory.Identity,
    ];

    const { data: inserted, error } = await supabase
      .from('requirements')
      .insert(
        categories.map((category) => ({
          application_id: applicationId,
          category,
          created_at: now,
        })),
      )
      .select(REQUIREMENT_COLUMNS);

    if (error) throw new Error(error.message);

    return (inserted ?? []).map((row) => enrichRequirement(row as Requirement, 'missing'));
  },

  /** Updates `requirement_status` rows based on uploaded documents. */
  async syncStatusFromDocuments(
    applicationId: string,
    documents: Document[],
  ): Promise<Requirement[]> {
    await requireUserId();

    const requirements = await this.listByApplication(applicationId);
    if (requirements.length === 0) return requirements;

    const requirementIds = requirements.map((req) => req.id);
    const { data: existingStatuses, error: statusError } = await supabase
      .from('requirement_status')
      .select(REQUIREMENT_STATUS_COLUMNS)
      .in('requirement_id', requirementIds);

    if (statusError) throw new Error(statusError.message);

    const existingByRequirement = new Map(
      (existingStatuses ?? []).map((row) => [row.requirement_id, row]),
    );

    for (const requirement of requirements) {
      const fulfilled = evaluateRequirementFulfillment(requirement.category, documents);
      const status: RequirementStatusValue = fulfilled ? 'fulfilled' : 'missing';
      const existing = existingByRequirement.get(requirement.id);

      if (existing) {
        if (existing.status !== status) {
          const { error } = await supabase
            .from('requirement_status')
            .update({ status })
            .eq('id', existing.id);

          if (error) throw new Error(error.message);
        }
      } else {
        const { error } = await supabase
          .from('requirement_status')
          .insert({ requirement_id: requirement.id, status });

        if (error) throw new Error(error.message);
      }
    }

    return this.listByApplication(applicationId);
  },
};
