"use client";

import { useActionState, useRef, useState } from "react";
import { useFormStatus } from "react-dom";
import { ArrowRight } from "lucide-react";
import {
  createProjectFromForm,
  type CreateProjectFormState,
} from "@/app/actions/projects";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

const SEED_PROMPTS = [
  "A smart self-watering planter that texts me when it's thirsty.",
  "A delivery drone that can carry a 1 kg payload across town.",
  "A custom robotic arm I can pose by hand and replay the motion.",
  "A wearable sensor that tracks posture and buzzes when I slouch.",
  "An industrial environmental sensor in a weatherproof enclosure.",
];

const MAX_PROMPT_LEN = 8000;

function SubmitButton({ disabled }: { disabled: boolean }) {
  const { pending } = useFormStatus();
  return (
    <Button
      type="submit"
      disabled={disabled || pending}
      className="h-11 rounded-full bg-white px-6 text-base font-medium text-neutral-950 hover:bg-neutral-200 disabled:opacity-60"
    >
      {pending ? "Starting…" : "Start project"}
      {!pending ? <ArrowRight className="ml-2 h-4 w-4" /> : null}
    </Button>
  );
}

export function NewProjectForm() {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [prompt, setPrompt] = useState("");
  const [state, formAction] = useActionState<
    CreateProjectFormState | null,
    FormData
  >(async (prev, formData) => createProjectFromForm(prev, formData), null);

  const trimmed = prompt.trim();
  const tooLong = prompt.length > MAX_PROMPT_LEN;
  const empty = trimmed.length === 0;

  function applySeed(text: string) {
    setPrompt(text);
    requestAnimationFrame(() => textareaRef.current?.focus());
  }

  return (
    <form action={formAction} className="flex flex-col gap-6">
      <div>
        <label htmlFor="prompt" className="sr-only">
          Describe what you want to build
        </label>
        <Textarea
          id="prompt"
          name="prompt"
          ref={textareaRef}
          required
          autoFocus
          rows={6}
          maxLength={MAX_PROMPT_LEN + 200}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="A smart planter that texts me when it's thirsty…"
          className="min-h-[180px] resize-y rounded-2xl border-neutral-800 bg-neutral-900/40 p-5 text-base text-white placeholder:text-neutral-500 focus-visible:ring-2 focus-visible:ring-white/30"
        />
        <div className="mt-2 flex items-center justify-between text-xs">
          <span className="text-neutral-500">
            Plain language. The agent decides what to ask back.
          </span>
          <span className={tooLong ? "text-red-400" : "text-neutral-500"}>
            {prompt.length.toLocaleString()} / {MAX_PROMPT_LEN.toLocaleString()}
          </span>
        </div>
      </div>

      <div>
        <p className="text-xs font-medium uppercase tracking-wider text-neutral-500">
          Try one of these
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {SEED_PROMPTS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => applySeed(s)}
              className="rounded-full border border-neutral-800 bg-neutral-900/40 px-3 py-1.5 text-xs text-neutral-300 transition-colors hover:border-neutral-700 hover:bg-neutral-900 hover:text-white"
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between gap-3 border-t border-neutral-900 pt-6">
        <p className="text-xs text-neutral-500">
          You can refine the prompt and re-run anytime.
        </p>
        <SubmitButton disabled={empty || tooLong} />
      </div>

      {state?.error ? (
        <p
          role="alert"
          className="rounded-lg border border-red-900/50 bg-red-950/40 px-4 py-3 text-sm text-red-300"
        >
          {state.error}
        </p>
      ) : null}
    </form>
  );
}
