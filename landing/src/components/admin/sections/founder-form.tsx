"use client";

import { useState, useTransition } from "react";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { SectionForm, FieldRow } from "@/components/admin/section-form";
import { uploadFounderPhoto } from "@/app/actions/upload";
import type { FounderContent } from "@/lib/content/types";

const inputCls =
  "border-neutral-800 bg-neutral-900/50 text-white placeholder:text-neutral-500";

export function FounderForm({ initial }: { initial: FounderContent }) {
  return (
    <SectionForm sectionKey="founder" initial={initial}>
      {(v, set) => (
        <>
          <FieldRow label="Photo">
            <PhotoUploader
              currentUrl={v.photo_url}
              onUploaded={(url) => set({ ...v, photo_url: url })}
              onClear={() => set({ ...v, photo_url: null })}
              initials={v.initials}
            />
          </FieldRow>
          <FieldRow label="Initials (used when no photo)" htmlFor="founder-initials">
            <Input
              id="founder-initials"
              value={v.initials}
              onChange={(e) => set({ ...v, initials: e.target.value })}
              maxLength={4}
              className={inputCls + " w-24"}
            />
          </FieldRow>
          <FieldRow
            label="Photo alt text"
            htmlFor="founder-photo-alt"
            hint="Used by screen readers and when the image fails to load."
          >
            <Input
              id="founder-photo-alt"
              value={v.photo_alt}
              onChange={(e) => set({ ...v, photo_alt: e.target.value })}
              className={inputCls}
            />
          </FieldRow>
          <FieldRow label="Eyebrow" htmlFor="founder-eyebrow">
            <Input
              id="founder-eyebrow"
              value={v.eyebrow}
              onChange={(e) => set({ ...v, eyebrow: e.target.value })}
              className={inputCls}
            />
          </FieldRow>
          <FieldRow label="Heading" htmlFor="founder-heading">
            <Textarea
              id="founder-heading"
              rows={2}
              value={v.heading}
              onChange={(e) => set({ ...v, heading: e.target.value })}
              className={inputCls}
            />
          </FieldRow>
          <FieldRow
            label="Paragraphs"
            hint="One paragraph per textarea. Click + to add another."
          >
            <div className="flex flex-col gap-3">
              {v.paragraphs.map((p, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <Textarea
                    rows={3}
                    value={p}
                    onChange={(e) => {
                      const next = [...v.paragraphs];
                      next[idx] = e.target.value;
                      set({ ...v, paragraphs: next });
                    }}
                    className={inputCls + " flex-1"}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => {
                      const next = v.paragraphs.filter((_, i) => i !== idx);
                      set({
                        ...v,
                        paragraphs: next.length ? next : [""],
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
                onClick={() => set({ ...v, paragraphs: [...v.paragraphs, ""] })}
                className="self-start border-neutral-800 bg-neutral-900/50 text-neutral-100 hover:bg-neutral-800 hover:text-white"
              >
                + Add paragraph
              </Button>
            </div>
          </FieldRow>
          <FieldRow label="Vision memo URL" htmlFor="founder-vision">
            <Input
              id="founder-vision"
              value={v.vision_memo_url}
              onChange={(e) => set({ ...v, vision_memo_url: e.target.value })}
              placeholder="https://… or leave # for placeholder"
              className={inputCls}
            />
          </FieldRow>
          <FieldRow
            label="“Read more” link label"
            htmlFor="founder-read-more"
          >
            <Input
              id="founder-read-more"
              value={v.read_more_label}
              onChange={(e) => set({ ...v, read_more_label: e.target.value })}
              className={inputCls}
            />
          </FieldRow>
        </>
      )}
    </SectionForm>
  );
}

function PhotoUploader({
  currentUrl,
  onUploaded,
  onClear,
  initials,
}: {
  currentUrl: string | null;
  onUploaded: (url: string) => void;
  onClear: () => void;
  initials: string;
}) {
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  function onChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    const fd = new FormData();
    fd.set("file", file);
    startTransition(async () => {
      const res = await uploadFounderPhoto(fd);
      if (res.ok) {
        onUploaded(res.url);
      } else {
        setError(res.error);
      }
    });
    e.target.value = "";
  }

  return (
    <div className="flex items-center gap-4">
      <div className="relative h-20 w-20 overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900">
        {currentUrl ? (
          // Plain img to avoid next/image domain whitelist friction in admin previews.
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={currentUrl}
            alt="Founder photo"
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-neutral-700 via-neutral-800 to-neutral-950 text-2xl font-semibold text-neutral-200/80">
            {initials}
          </div>
        )}
      </div>
      <div className="flex flex-col gap-2">
        <label className="cursor-pointer rounded-md border border-neutral-800 bg-neutral-900/50 px-3 py-1.5 text-sm text-neutral-100 transition-colors hover:bg-neutral-800">
          {pending ? "Uploading…" : "Upload photo"}
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            disabled={pending}
            onChange={onChange}
            className="sr-only"
          />
        </label>
        {currentUrl ? (
          <button
            type="button"
            onClick={onClear}
            className="text-left text-xs text-neutral-500 hover:text-red-400"
          >
            Remove photo
          </button>
        ) : null}
        {error ? (
          <p className="text-xs text-red-400" role="alert">
            {error}
          </p>
        ) : null}
        <p className="text-xs text-neutral-500">JPG, PNG, or WebP. Max 5 MB.</p>
      </div>
    </div>
  );
}
