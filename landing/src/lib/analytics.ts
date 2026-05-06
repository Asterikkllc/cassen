import posthog from "posthog-js";

// PostHog initialization happens in `src/instrumentation-client.ts`.
// This file just exposes a thin `track()` wrapper that's a no-op when the
// project token isn't configured (so dev without env vars doesn't error).

export function track(
  event: string,
  properties?: Record<string, unknown>,
): void {
  if (typeof window === "undefined") return;
  if (!process.env.NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN) return;
  posthog.capture(event, properties);
}
