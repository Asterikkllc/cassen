"use client";

import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { SectionForm, FieldRow } from "@/components/admin/section-form";
import type { MetaContent } from "@/lib/content/types";

const inputCls =
  "border-neutral-800 bg-neutral-900/50 text-white placeholder:text-neutral-500";

export function MetaForm({ initial }: { initial: MetaContent }) {
  return (
    <SectionForm sectionKey="meta" initial={initial}>
      {(v, set) => (
        <>
          <FieldRow
            label="Page title"
            hint="Shown in browser tabs and search results."
          >
            <Input
              value={v.title}
              onChange={(e) => set({ ...v, title: e.target.value })}
              className={inputCls}
            />
          </FieldRow>
          <FieldRow
            label="Meta description"
            hint="The 1–2 sentence preview shown by search engines and social previews."
          >
            <Textarea
              rows={3}
              value={v.description}
              onChange={(e) => set({ ...v, description: e.target.value })}
              className={inputCls}
            />
          </FieldRow>
        </>
      )}
    </SectionForm>
  );
}
