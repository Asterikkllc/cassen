"use client";

import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { SectionForm, FieldRow } from "@/components/admin/section-form";
import type { SignupContent } from "@/lib/content/types";

const inputCls =
  "border-neutral-800 bg-neutral-900/50 text-white placeholder:text-neutral-500";

export function SignupSettingsForm({ initial }: { initial: SignupContent }) {
  return (
    <SectionForm sectionKey="signup" initial={initial}>
      {(v, set) => (
        <>
          <FieldRow label="Email placeholder">
            <Input
              value={v.email_placeholder}
              onChange={(e) =>
                set({ ...v, email_placeholder: e.target.value })
              }
              className={inputCls}
            />
          </FieldRow>
          <FieldRow label="Submit button label">
            <Input
              value={v.submit_label}
              onChange={(e) => set({ ...v, submit_label: e.target.value })}
              className={inputCls}
            />
          </FieldRow>
          <FieldRow label="Submit button label (while sending)">
            <Input
              value={v.submit_pending_label}
              onChange={(e) =>
                set({ ...v, submit_pending_label: e.target.value })
              }
              className={inputCls}
            />
          </FieldRow>

          <div className="rounded-xl border border-neutral-800 bg-neutral-900/30 p-4">
            <p className="text-xs font-medium uppercase tracking-wider text-neutral-400">
              Success state (shown after a signup completes)
            </p>
            <div className="mt-4 flex flex-col gap-4">
              <FieldRow label="Success heading">
                <Input
                  value={v.success_heading}
                  onChange={(e) =>
                    set({ ...v, success_heading: e.target.value })
                  }
                  className={inputCls}
                />
              </FieldRow>
              <FieldRow
                label="Position template"
                hint="Use {position} and it'll be replaced with the signup number."
              >
                <Input
                  value={v.success_position_template}
                  onChange={(e) =>
                    set({ ...v, success_position_template: e.target.value })
                  }
                  className={inputCls}
                />
              </FieldRow>
              <FieldRow label="Success body">
                <Textarea
                  rows={3}
                  value={v.success_body}
                  onChange={(e) =>
                    set({ ...v, success_body: e.target.value })
                  }
                  className={inputCls}
                />
              </FieldRow>
              <FieldRow label="Share button label">
                <Input
                  value={v.share_label}
                  onChange={(e) => set({ ...v, share_label: e.target.value })}
                  className={inputCls}
                />
              </FieldRow>
              <FieldRow
                label="Share tweet text"
                hint="Pre-fills the X/Twitter compose window when someone clicks share."
              >
                <Textarea
                  rows={2}
                  value={v.share_text}
                  onChange={(e) => set({ ...v, share_text: e.target.value })}
                  className={inputCls}
                />
              </FieldRow>
            </div>
          </div>

          <div className="rounded-xl border border-neutral-800 bg-neutral-900/30 p-4">
            <p className="text-xs font-medium uppercase tracking-wider text-neutral-400">
              Error messages
            </p>
            <div className="mt-4 flex flex-col gap-4">
              <FieldRow label="Invalid email">
                <Input
                  value={v.error_invalid_email}
                  onChange={(e) =>
                    set({ ...v, error_invalid_email: e.target.value })
                  }
                  className={inputCls}
                />
              </FieldRow>
              <FieldRow label="Already on the list">
                <Input
                  value={v.error_duplicate}
                  onChange={(e) =>
                    set({ ...v, error_duplicate: e.target.value })
                  }
                  className={inputCls}
                />
              </FieldRow>
              <FieldRow label="Generic error">
                <Input
                  value={v.error_generic}
                  onChange={(e) =>
                    set({ ...v, error_generic: e.target.value })
                  }
                  className={inputCls}
                />
              </FieldRow>
              <FieldRow label="Not configured (env missing)">
                <Input
                  value={v.error_not_configured}
                  onChange={(e) =>
                    set({ ...v, error_not_configured: e.target.value })
                  }
                  className={inputCls}
                />
              </FieldRow>
            </div>
          </div>
        </>
      )}
    </SectionForm>
  );
}
