import { RequirementCategory } from '@/constants/requirementCategories';
import type { Application } from '@/types/application';
import type { Requirement } from '@/types/requirement';

/** Days remaining until the application deadline, or null if no deadline. */
export function computeDaysUntilDeadline(deadline: string | null): number | null {
  if (!deadline) return null;

  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const deadlineDate = new Date(deadline);
  deadlineDate.setHours(0, 0, 0, 0);

  const diffMs = deadlineDate.getTime() - now.getTime();
  return Math.max(0, Math.ceil(diffMs / (1000 * 60 * 60 * 24)));
}

/** Count required document requirements that are not yet fulfilled. */
export function countMissingDocuments(requirements: Requirement[]): number {
  return requirements.filter(
    (req) =>
      req.category === RequirementCategory.Documents &&
      req.is_required &&
      !req.is_fulfilled,
  ).length;
}

/** Derive a display name for an application. */
export function getApplicationDisplayName(application: Application): string {
  return application.title?.trim() || 'Untitled Application';
}
