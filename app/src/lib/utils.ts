import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * `cn` — the single-line class composition helper every shadcn /
 * Base UI primitive expects. Merges Tailwind classes intelligently
 * (so `px-2 px-4` collapses to `px-4`).
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
