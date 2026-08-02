// TODO: Add slug generation for storage paths
// TODO: Add file size formatting and validation helpers

/**
 * Returns a promise that resolves after the given milliseconds.
 * Useful for simulating async delays during development.
 */
export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Generates a random alphanumeric ID string.
 */
export function generateId(length = 12): string {
  return Math.random()
    .toString(36)
    .substring(2, 2 + length);
}

/**
 * Safely parses JSON without throwing.
 */
export function safeJsonParse<T>(value: string, fallback: T): T {
  try {
    return JSON.parse(value) as T;
  } catch {
    return fallback;
  }
}

/**
 * Returns the file extension from a filename (lowercase, without dot).
 */
export function getFileExtension(filename: string): string | null {
  const parts = filename.split('.');
  if (parts.length < 2) return null;
  return parts.pop()?.toLowerCase() ?? null;
}

/**
 * Formats byte size into a human-readable string.
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  const size = bytes / Math.pow(1024, i);
  return `${size.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

/**
 * Type guard to check if a value is a non-null object.
 */
export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/**
 * Omits undefined values from an object (useful for Supabase partial updates).
 */
export function omitUndefined<T extends Record<string, unknown>>(obj: T): Partial<T> {
  return Object.fromEntries(
    Object.entries(obj).filter(([, v]) => v !== undefined),
  ) as Partial<T>;
}
