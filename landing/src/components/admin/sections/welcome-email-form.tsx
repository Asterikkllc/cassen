"use client";

import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { SectionForm, FieldRow } from "@/components/admin/section-form";
import type { WelcomeEmailContent } from "@/lib/content/types";

const inputCls =
  "border-neutral-800 bg-neutral-900/50 text-white placeholder:text-neutral-500";

export function WelcomeEmailForm({
  initial,
}: {
  initial: WelcomeEmailContent;
}) {
  return (
    <SectionForm sectionKey="welcome_email" initial={initial}>
      {(v, set) => (
        <>
          <FieldRow label="Subject line">
            <Input
              value={v.subject}
              onChange={(e) => set({ ...v, subject: e.target.value })}
              className={inputCls}
            />
          </FieldRow>
          <FieldRow label="Greeting">
            <Input
              value={v.greeting}
              onChange={(e) => set({ ...v, greeting: e.target.value })}
              placeholder="Hey,"
              className={inputCls}
            />
          </FieldRow>
          <FieldRow
            label="Position line template"
            hint="Use {position} and it'll be replaced with the signup number."
          >
            <Textarea
              rows={2}
              value={v.position_line_template}
              onChange={(e) =>
                set({ ...v, position_line_template: e.target.value })
              }
              className={inputCls}
            />
          </FieldRow>
          <FieldRow
            label="Body paragraphs"
            hint="One paragraph per textarea. They render in order, between the position line and signature."
          >
            <div className="flex flex-col gap-3">
              {v.body_paragraphs.map((p, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <Textarea
                    rows={3}
                    value={p}
                    onChange={(e) => {
                      const next = [...v.body_paragraphs];
                      next[idx] = e.target.value;
                      set({ ...v, body_paragraphs: next });
                    }}
                    className={inputCls + " flex-1"}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => {
                      const next = v.body_paragraphs.filter((_, i) => i !== idx);
                      set({
                        ...v,
                        body_paragraphs: next.length ? next : [""],
                      });
                    }}
                    className="text-neutral-500 hover:text-red-400"
                  >
                    Remove
                  </Button>
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                onClick={() =>
                  set({ ...v, body_paragraphs: [...v.body_paragraphs, ""] })
                }
                className="self-start border-neutral-800 bg-neutral-900/50 text-neutral-100 hover:bg-neutral-800 hover:text-white"
              >
                + Add paragraph
              </Button>
            </div>
          </FieldRow>
          <FieldRow label="Signature">
            <Input
              value={v.signature}
              onChange={(e) => set({ ...v, signature: e.target.value })}
              placeholder="Evelyn, building Cassen"
              className={inputCls}
            />
          </FieldRow>
          <FieldRow
            label="Footer disclaimer"
            hint="Small print at the bottom of the email."
          >
            <Textarea
              rows={2}
              value={v.footer_disclaimer}
              onChange={(e) =>
                set({ ...v, footer_disclaimer: e.target.value })
              }
              className={inputCls}
            />
          </FieldRow>
        </>
      )}
    </SectionForm>
  );
}
