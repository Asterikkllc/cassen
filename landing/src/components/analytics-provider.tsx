"use client";

import { MotionConfig } from "motion/react";

// PostHog initialization moved to `src/instrumentation-client.ts` (Next 15.3+
// convention — runs earlier than a React useEffect). This component now only
// wraps the app in MotionConfig to honor `prefers-reduced-motion`.
export function AnalyticsProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  return <MotionConfig reducedMotion="user">{children}</MotionConfig>;
}
