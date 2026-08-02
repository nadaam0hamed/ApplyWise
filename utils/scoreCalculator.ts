import type { ChecklistEntry } from '@/types/analysis';
import type { Requirement } from '@/types/requirement';

// TODO: Weight document types by priority when calculating readiness
// TODO: Factor in deadline proximity for urgency scoring

/** Weights applied per missing document priority. */
const PRIORITY_WEIGHTS = {
  high: 15,
  medium: 10,
  low: 5,
} as const;

/**
 * Calculates application readiness score (0–100) from checklist completion.
 */
export function calculateReadinessFromChecklist(checklist: ChecklistEntry[]): number {
  if (checklist.length === 0) return 0;
  const completed = checklist.filter((item) => item.completed).length;
  return Math.round((completed / checklist.length) * 100);
}

/**
 * Calculates readiness from fulfilled vs total requirements.
 */
export function calculateReadinessFromRequirements(requirements: Requirement[]): number {
  const required = requirements.filter((r) => r.is_required);
  if (required.length === 0) return 100;
  const fulfilled = required.filter((r) => r.is_fulfilled).length;
  return Math.round((fulfilled / required.length) * 100);
}

/**
 * Deducts points from a base score based on missing document priorities.
 */
export function applyMissingDocumentPenalty(
  baseScore: number,
  missing: Array<{ priority: keyof typeof PRIORITY_WEIGHTS }>,
): number {
  const penalty = missing.reduce(
    (sum, doc) => sum + PRIORITY_WEIGHTS[doc.priority],
    0,
  );
  return Math.max(0, Math.min(100, baseScore - penalty));
}

/**
 * Clamps a score value to the 0–100 range.
 */
export function clampScore(score: number): number {
  return Math.max(0, Math.min(100, Math.round(score)));
}
