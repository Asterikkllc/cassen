"use client";

import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { SectionForm, FieldRow } from "@/components/admin/section-form";
import { ICON_NAMES } from "@/lib/content/icons";
import type {
  FaqContent,
  HowItWorksContent,
  UseCasesContent,
} from "@/lib/content/types";

const inputCls =
  "border-neutral-800 bg-neutral-900/50 text-white placeholder:text-neutral-500";
const selectCls =
  "h-10 rounded-md border border-neutral-800 bg-neutral-900/50 px-3 text-sm text-white";

export function HowItWorksForm({ initial }: { initial: HowItWorksContent }) {
  return (
    <SectionForm sectionKey="how_it_works" initial={initial}>
      {(v, set) => (
        <>
          <Header v={v} set={set} />
          <FieldRow label="Steps">
            <div className="flex flex-col gap-4">
              {v.steps.map((step, idx) => (
                <div
                  key={idx}
                  className="rounded-xl border border-neutral-800 bg-neutral-900/30 p-4"
                >
                  <div className="grid grid-cols-2 gap-3">
                    <Input
                      placeholder="Number (e.g. 01)"
                      value={step.number}
                      onChange={(e) => {
                        const next = [...v.steps];
                        next[idx] = { ...step, number: e.target.value };
                        set({ ...v, steps: next });
                      }}
                      className={inputCls}
                    />
                    <select
                      value={step.icon}
                      onChange={(e) => {
                        const next = [...v.steps];
                        next[idx] = { ...step, icon: e.target.value };
                        set({ ...v, steps: next });
                      }}
                      className={selectCls}
                    >
                      {ICON_NAMES.map((n) => (
                        <option key={n} value={n}>
                          {n}
                        </option>
                      ))}
                    </select>
                  </div>
                  <Input
                    placeholder="Title"
                    value={step.title}
                    onChange={(e) => {
                      const next = [...v.steps];
                      next[idx] = { ...step, title: e.target.value };
                      set({ ...v, steps: next });
                    }}
                    className={inputCls + " mt-3"}
                  />
                  <Textarea
                    placeholder="Body"
                    rows={2}
                    value={step.body}
                    onChange={(e) => {
                      const next = [...v.steps];
                      next[idx] = { ...step, body: e.target.value };
                      set({ ...v, steps: next });
                    }}
                    className={inputCls + " mt-3"}
                  />
                  <div className="mt-3 flex items-center justify-between">
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={() => {
                        const next = v.steps.filter((_, i) => i !== idx);
                        set({ ...v, steps: next.length ? next : v.steps });
                      }}
                      className="text-neutral-500 hover:text-red-400"
                    >
                      Remove step
                    </Button>
                  </div>
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                onClick={() =>
                  set({
                    ...v,
                    steps: [
                      ...v.steps,
                      { number: "", icon: "Box", title: "", body: "" },
                    ],
                  })
                }
                className="self-start border-neutral-800 bg-neutral-900/50 text-neutral-100 hover:bg-neutral-800 hover:text-white"
              >
                + Add step
              </Button>
            </div>
          </FieldRow>
        </>
      )}
    </SectionForm>
  );
}

function Header<T extends { eyebrow: string; headline: string; subhead?: string }>({
  v,
  set,
}: {
  v: T;
  set: (next: T) => void;
}) {
  return (
    <>
      <FieldRow label="Eyebrow">
        <Input
          value={v.eyebrow}
          onChange={(e) => set({ ...v, eyebrow: e.target.value })}
          className={inputCls}
        />
      </FieldRow>
      <FieldRow label="Headline">
        <Textarea
          rows={2}
          value={v.headline}
          onChange={(e) => set({ ...v, headline: e.target.value })}
          className={inputCls}
        />
      </FieldRow>
      {"subhead" in v ? (
        <FieldRow label="Subhead">
          <Textarea
            rows={2}
            value={v.subhead ?? ""}
            onChange={(e) => set({ ...v, subhead: e.target.value })}
            className={inputCls}
          />
        </FieldRow>
      ) : null}
    </>
  );
}

export function UseCasesForm({ initial }: { initial: UseCasesContent }) {
  return (
    <SectionForm sectionKey="use_cases" initial={initial}>
      {(v, set) => (
        <>
          <Header v={v} set={set} />
          <FieldRow label="Items">
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {v.items.map((item, idx) => (
                <div
                  key={idx}
                  className="rounded-xl border border-neutral-800 bg-neutral-900/30 p-4"
                >
                  <select
                    value={item.icon}
                    onChange={(e) => {
                      const next = [...v.items];
                      next[idx] = { ...item, icon: e.target.value };
                      set({ ...v, items: next });
                    }}
                    className={selectCls + " w-full"}
                  >
                    {ICON_NAMES.map((n) => (
                      <option key={n} value={n}>
                        {n}
                      </option>
                    ))}
                  </select>
                  <Input
                    placeholder="Title"
                    value={item.title}
                    onChange={(e) => {
                      const next = [...v.items];
                      next[idx] = { ...item, title: e.target.value };
                      set({ ...v, items: next });
                    }}
                    className={inputCls + " mt-3"}
                  />
                  <Textarea
                    placeholder="Body"
                    rows={2}
                    value={item.body}
                    onChange={(e) => {
                      const next = [...v.items];
                      next[idx] = { ...item, body: e.target.value };
                      set({ ...v, items: next });
                    }}
                    className={inputCls + " mt-3"}
                  />
                  <div className="mt-3">
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={() => {
                        const next = v.items.filter((_, i) => i !== idx);
                        set({ ...v, items: next.length ? next : v.items });
                      }}
                      className="text-neutral-500 hover:text-red-400"
                    >
                      Remove item
                    </Button>
                  </div>
                </div>
              ))}
            </div>
            <Button
              type="button"
              variant="outline"
              onClick={() =>
                set({
                  ...v,
                  items: [
                    ...v.items,
                    { icon: "Box", title: "", body: "" },
                  ],
                })
              }
              className="mt-4 self-start border-neutral-800 bg-neutral-900/50 text-neutral-100 hover:bg-neutral-800 hover:text-white"
            >
              + Add item
            </Button>
          </FieldRow>
        </>
      )}
    </SectionForm>
  );
}

export function FaqForm({ initial }: { initial: FaqContent }) {
  return (
    <SectionForm sectionKey="faq" initial={initial}>
      {(v, set) => (
        <>
          <FieldRow label="Eyebrow">
            <Input
              value={v.eyebrow}
              onChange={(e) => set({ ...v, eyebrow: e.target.value })}
              className={inputCls}
            />
          </FieldRow>
          <FieldRow label="Headline">
            <Textarea
              rows={2}
              value={v.headline}
              onChange={(e) => set({ ...v, headline: e.target.value })}
              className={inputCls}
            />
          </FieldRow>
          <FieldRow label="Q & A">
            <div className="flex flex-col gap-4">
              {v.items.map((qa, idx) => (
                <div
                  key={idx}
                  className="rounded-xl border border-neutral-800 bg-neutral-900/30 p-4"
                >
                  <Input
                    placeholder="Question"
                    value={qa.q}
                    onChange={(e) => {
                      const next = [...v.items];
                      next[idx] = { ...qa, q: e.target.value };
                      set({ ...v, items: next });
                    }}
                    className={inputCls}
                  />
                  <Textarea
                    placeholder="Answer"
                    rows={3}
                    value={qa.a}
                    onChange={(e) => {
                      const next = [...v.items];
                      next[idx] = { ...qa, a: e.target.value };
                      set({ ...v, items: next });
                    }}
                    className={inputCls + " mt-3"}
                  />
                  <div className="mt-3">
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={() => {
                        const next = v.items.filter((_, i) => i !== idx);
                        set({ ...v, items: next.length ? next : v.items });
                      }}
                      className="text-neutral-500 hover:text-red-400"
                    >
                      Remove
                    </Button>
                  </div>
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                onClick={() =>
                  set({ ...v, items: [...v.items, { q: "", a: "" }] })
                }
                className="self-start border-neutral-800 bg-neutral-900/50 text-neutral-100 hover:bg-neutral-800 hover:text-white"
              >
                + Add Q&A
              </Button>
            </div>
          </FieldRow>
        </>
      )}
    </SectionForm>
  );
}
