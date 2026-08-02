// TODO: Add locale-aware date formatting for dashboard and report views
// TODO: Support relative time labels (e.g. "3 days left")

/**
 * Formats an ISO date string or Date object for display.
 * @param date - ISO string or Date instance
 * @param locale - BCP 47 locale tag (defaults to 'en-US')
 */
export function formatDate(
  date: string | Date,
  locale = 'en-US',
): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

/**
 * Formats a date as ISO date only (YYYY-MM-DD) for Supabase date columns.
 */
export function toISODateString(date: Date): string {
  return date.toISOString().split('T')[0];
}

/**
 * Returns the number of days between today and a target date.
 * Negative values indicate the date has passed.
 */
export function daysUntil(date: string | Date): number {
  const target = typeof date === 'string' ? new Date(date) : date;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  target.setHours(0, 0, 0, 0);
  const diffMs = target.getTime() - today.getTime();
  return Math.ceil(diffMs / (1000 * 60 * 60 * 24));
}
