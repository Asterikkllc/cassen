"use client";

import { useState, useTransition } from "react";
import { saveSectionAction } from "@/app/actions/content";
import { Button } from "@/components/ui/button";
import type { SectionKey, SiteContent } from "@/lib/content/types";

type Props<K extends SectionKey> = {
  sectionKey: K;
  initial: SiteContent[K];
  children: (
    value: SiteContent[K],
    set: (next: SiteContent[K]) => void,
  ) => React.ReactNode;
};

export function SectionForm<K extends SectionKey>({
  sectionKey,
  initial,
  children,
}: Props<K>) {
  const [value, setValue] = useState<SiteContent[K]>(initial);
  const [pending, startTransition] = useTransition();
  const [feedback, setFeedback] = useState<{
    kind: "ok" | "err";
    msg: string;
  } | null>(null);

  function onSave() {
    startTransition(async () => {
      setFeedback(null);
      const res = await saveSectionAction(sectionKey, value);
      if (res.ok) {
        setFeedback({ kind: "ok", msg: "Saved." });
      } else {
        setFeedback({ kind: "err", msg: res.error });
      }
    });
  }

  function onReset() {
    setValue(initial);
    setFeedback(null);
  }

  return (
    <div className="flex flex-col gap-6">
      {children(value, setValue)}
      <div className="flex items-center gap-3 border-t border-neutral-800 pt-6">
        <Button
          onClick={onSave}
          disabled={pending}
          className="h-10 bg-white px-5 text-neutral-950 hover:bg-neutral-200 disabled:opacity-60"
        >
          {pending ? "Saving…" : "Save changes"}
        </Button>
        <Button
          onClick={onReset}
          disabled={pending}
          variant="ghost"
          className="text-neutral-400 hover:text-white"
        >
          Reset
        </Button>
        {feedback ? (
          <span
            className={
              feedback.kind === "ok"
                ? "text-sm text-emerald-400"
                : "text-sm text-red-400"
            }
            role="status"
          >
            {feedback.msg}
          </span>
        ) : null}
      </div>
    </div>
  );
}

export function FieldRow({
  label,
  htmlFor,
  hint,
  children,
}: {
  label: string;
  htmlFor?: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      <label
        htmlFor={htmlFor}
        className="text-xs font-medium uppercase tracking-wider text-neutral-400"
      >
        {label}
      </label>
      {children}
      {hint ? <p className="text-xs text-neutral-500">{hint}</p> : null}
    </div>
  );
}
