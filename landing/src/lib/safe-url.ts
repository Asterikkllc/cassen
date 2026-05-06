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
  if (trimmed.startsWith("/") && !trimmed.startsWith("//")) return trimmed;
  return fallback;
}
