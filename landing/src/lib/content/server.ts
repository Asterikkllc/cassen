import "server-only";
import { cache } from "react";
import { getSupabaseAdmin } from "@/lib/supabase";
import { DEFAULT_CONTENT } from "./defaults";
import type { SectionKey, SiteContent } from "./types";

type Row = { key: string; value: unknown };

export const getSiteContent = cache(async (): Promise<SiteContent> => {
  let rows: Row[] = [];
  try {
    const supabase = getSupabaseAdmin();
    const { data, error } = await supabase
      .from("site_content")
      .select("key, value");
    if (error) {
      console.warn("[content] supabase error, falling back to defaults:", error.message);
    } else {
      rows = (data ?? []) as Row[];
    }
  } catch (err) {
    console.warn("[content] env not configured, falling back to defaults", err);
  }

  const overrides = new Map(rows.map((r) => [r.key, r.value]));

  const merged: SiteContent = { ...DEFAULT_CONTENT };
  for (const key of Object.keys(merged) as SectionKey[]) {
    const v = overrides.get(key);
    if (v && typeof v === "object") {
      // Shallow merge so partial overrides keep default fields they don't touch.
      // Cast through unknown — we trust DB shape because writes go through the
      // Zod-validated saveSectionAction.
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (merged[key] as any) = { ...merged[key], ...(v as object) };
    }
  }
  return merged;
});

export async function getSection<K extends SectionKey>(
  key: K,
): Promise<SiteContent[K]> {
  const content = await getSiteContent();
  return content[key];
}
