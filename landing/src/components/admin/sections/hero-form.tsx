"use client";

import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { SectionForm, FieldRow } from "@/components/admin/section-form";
import type { HeroContent } from "@/lib/content/types";

const inputCls =
  "border-neutral-800 bg-neutral-900/50 text-white placeholder:text-neutral-500";

export function HeroForm({ initial }: { initial: HeroContent }) {
  return (
    <SectionForm sectionKey="hero" initial={initial}>
      {(v, set) => (
        <>
          <FieldRow label="Badge" htmlFor="hero-badge">
            <Input
              id="hero-badge"
              value={v.badge}
              onChange={(e) => set({ ...v, badge: e.target.value })}
              className={inputCls}
            />
          </FieldRow>
          <FieldRow label="Headline" htmlFor="hero-headline">
            <Textarea
              id="hero-headline"
              rows={2}
              value={v.headline}
              onChange={(e) => set({ ...v, headline: e.target.value })}
              className={inputCls}
            />
          </FieldRow>
          <FieldRow label="Subheadline" htmlFor="hero-sub">
            <Textarea
              id="hero-sub"
              rows={3}
              value={v.subheadline}
              onChange={(e) => set({ ...v, subheadline: e.target.value })}
              className={inputCls}
            />
          </FieldRow>
          <FieldRow label="Trust line" htmlFor="hero-trust">
            <Input
              id="hero-trust"
              value={v.trust_line}
              onChange={(e) => set({ ...v, trust_line: e.target.value })}
              className={inputCls}
            />
          </FieldRow>
        </>
      )}
    </SectionForm>
  );
}
