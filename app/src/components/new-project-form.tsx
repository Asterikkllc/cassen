"use client";

import { useActionState, useRef, useState } from "react";
import { useFormStatus } from "react-dom";
import { ArrowUp, Loader2, Sparkles } from "lucide-react";
import {
  createProjectFromForm,
  type CreateProjectFormState,
} from "@/app/actions/projects";

const SEED_PROMPTS = [
  "A smart self-watering planter that texts me when it's thirsty.",
  "A delivery drone that can carry a 1 kg payload across town.",
  "A custom robotic arm I can pose by hand and replay the motion.",
  "A wearable sensor that tracks posture and buzzes when I slouch.",
  "An industrial environmental sensor in a weatherproof enclosure.",
];

const MAX_PROMPT_LEN = 8000;

function SendButton({ disabled }: { disabled: boolean }) {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={disabled || pending}
      aria-label="Start project"
      className="grid h-9 w-9 flex-shrink-0 place-items-center rounded-full bg-primary text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:bg-muted disabled:text-muted-foreground"
    >
      {pending ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <ArrowUp className="h-4 w-4" />
      )}
    </button>
  );
}

/**
 * Chat-style entry for new projects. Single big textarea + send;
 * mirrors the in-project ChatThread footer so the transition into
 * the project conversation feels seamless. Submit creates the
 * project row, seeds the user's prompt as the first message, and
 * redirects to /projects/[id].
 */
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
    <div className="mx-auto flex h-full w-full max-w-3xl flex-col px-4 sm:px-6">
      <div className="flex-1" />

      <div className="flex flex-col items-center gap-3 pb-8 text-center">
        <span className="inline-flex items-center gap-1.5 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.2em] text-primary">
          <Sparkles className="h-3 w-3" />
          New project
        </span>
        <h1 className="text-balance text-3xl font-semibold tracking-tight md:text-4xl">
          What do you want to build?
        </h1>
        <p className="max-w-md text-pretty text-sm text-muted-foreground">
          One paragraph is plenty. Describe the product in plain language —
          form, function, constraints. The agent decides what to ask back.
        </p>
      </div>

      <form action={formAction} className="flex flex-col gap-3 pb-10">
        <div className="flex items-end gap-2 rounded-2xl border border-border bg-card/80 px-3 py-2 focus-within:border-primary/40">
          <textarea
            id="prompt"
            name="prompt"
            ref={textareaRef}
            required
            autoFocus
            rows={1}
            maxLength={MAX_PROMPT_LEN + 200}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey && !empty && !tooLong) {
                e.preventDefault();
                (e.currentTarget.form as HTMLFormElement | null)?.requestSubmit();
              }
            }}
            placeholder="A smart planter that texts me when it's thirsty…"
            className="max-h-48 min-h-9 flex-1 resize-none bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
          />
          <SendButton disabled={empty || tooLong} />
        </div>

        <div className="flex items-center justify-between gap-3 text-[10px] text-muted-foreground">
          <span>
            Enter to start · Shift+Enter for newline · One paragraph is plenty
          </span>
          <span className={tooLong ? "text-destructive" : "text-muted-foreground"}>
            {prompt.length.toLocaleString()} / {MAX_PROMPT_LEN.toLocaleString()}
          </span>
        </div>

        <div className="mt-2">
          <p className="px-1 text-[10px] font-medium uppercase tracking-[0.2em] text-muted-foreground">
            Try one of these
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            {SEED_PROMPTS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => applySeed(s)}
                className="max-w-full truncate rounded-full border border-border bg-card/40 px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:bg-card hover:text-foreground"
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {state?.error ? (
          <p
            role="alert"
            className="mt-2 rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive"
          >
            {state.error}
          </p>
        ) : null}
      </form>
    </div>
  );
}
