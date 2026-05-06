// Defensive URL helpers. The DB Zod validation is the primary gate; these
// runtime guards exist so a stale row written before the validators don't bite.

const HREF_SCHEMES = /^(https?:|mailto:|#|\/)/i;

export function safeHref(value: string | null | undefined, fallback = "#"): string {
  if (!value) return fallback;
  const trimmed = value.trim();
  if (!trimmed) return fallback;
  if (trimmed.startsWith("/") && !trimmed.startsWith("//")) return trimmed;
  if (trimmed === "#" || trimmed.startsWith("#")) return trimmed;
  if (HREF_SCHEMES.test(trimmed)) return trimmed;
  return fallback;
}

// True when a URL is meaningful enough to render a clickable link for —
// i.e. not empty, not whitespace, not the bare `#` placeholder.
export function hasRealUrl(value: string | null | undefined): boolean {
  if (!value) return false;
  const trimmed = value.trim();
  return trimmed.length > 0 && trimmed !== "#";
}

export function safeRedirectPath(
  value: string | null | undefined,
  fallback: string,
): string {
  if (!value) return fallback;
  const trimmed = value.trim();
  // Only same-origin relative paths. Reject protocol-relative `//x` and absolute URLs.
  if (trimmed.startsWith("/") && !trimmed.startsWith("//")) return trimmed;
  return fallback;
}
