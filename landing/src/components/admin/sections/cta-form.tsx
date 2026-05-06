"use client";

import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { SectionForm, FieldRow } from "@/components/admin/section-form";
import type { CtaContent, FooterContent } from "@/lib/content/types";

const inputCls =
  "border-neutral-800 bg-neutral-900/50 text-white placeholder:text-neutral-500";

export function CtaForm({ initial }: { initial: CtaContent }) {
  return (
    <SectionForm sectionKey="cta" initial={initial}>
      {(v, set) => (
        <>
          <FieldRow label="Headline">
            <Textarea
              rows={2}
              value={v.headline}
              onChange={(e) => set({ ...v, headline: e.target.value })}
              className={inputCls}
            />
          </FieldRow>
          <FieldRow label="Subheadline">
            <Textarea
              rows={2}
              value={v.subheadline}
              onChange={(e) => set({ ...v, subheadline: e.target.value })}
              className={inputCls}
            />
          </FieldRow>
          <FieldRow label="Trust line">
            <Input
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

export function FooterForm({ initial }: { initial: FooterContent }) {
  return (
    <SectionForm sectionKey="footer" initial={initial}>
      {(v, set) => (
        <>
          <FieldRow label="Wordmark">
            <Input
              value={v.wordmark}
              onChange={(e) => set({ ...v, wordmark: e.target.value })}
              placeholder="Cassen"
              className={inputCls}
            />
          </FieldRow>
          <FieldRow label="Tagline">
            <Input
              value={v.tagline}
              onChange={(e) => set({ ...v, tagline: e.target.value })}
              placeholder="Made with care"
              className={inputCls}
            />
          </FieldRow>
          <FieldRow label="Vision URL">
            <Input
              value={v.vision_url}
              onChange={(e) => set({ ...v, vision_url: e.target.value })}
              placeholder="https://…"
              className={inputCls}
            />
          </FieldRow>
          <FieldRow label="Vision link label">
            <Input
              value={v.vision_label}
              onChange={(e) => set({ ...v, vision_label: e.target.value })}
              placeholder="Vision"
              className={inputCls}
            />
          </FieldRow>
          <FieldRow label="Contact email">
            <Input
              value={v.contact_email}
              onChange={(e) => set({ ...v, contact_email: e.target.value })}
              placeholder="hello@cassen.ai"
              className={inputCls}
            />
          </FieldRow>
          <FieldRow label="Contact link label">
            <Input
              value={v.contact_label}
              onChange={(e) => set({ ...v, contact_label: e.target.value })}
              placeholder="Contact"
              className={inputCls}
            />
          </FieldRow>
          <FieldRow label="X / Twitter URL">
            <Input
              value={v.twitter_url}
              onChange={(e) => set({ ...v, twitter_url: e.target.value })}
              placeholder="https://twitter.com/…"
              className={inputCls}
            />
          </FieldRow>
          <FieldRow label="X / Twitter link label">
            <Input
              value={v.twitter_label}
              onChange={(e) => set({ ...v, twitter_label: e.target.value })}
              placeholder="X / Twitter"
              className={inputCls}
            />
          </FieldRow>
          <FieldRow
            label="Copyright template"
            hint="Use {year} and it'll be replaced at render time."
          >
            <Input
              value={v.copyright_template}
              onChange={(e) =>
                set({ ...v, copyright_template: e.target.value })
              }
              placeholder="© {year} Cassen. All rights reserved."
              className={inputCls}
            />
          </FieldRow>
        </>
      )}
    </SectionForm>
  );
}
