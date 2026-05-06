"use client";

import { useActionState, useEffect, useRef } from "react";
import { useFormStatus } from "react-dom";
import { signupAction, type SignupResult } from "@/app/actions/signup";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SignupSuccess } from "@/components/signup-success";
import { track } from "@/lib/analytics";
import { cn } from "@/lib/utils";
import type { SignupContent } from "@/lib/content/types";

function SubmitButton({
  label,
  pendingLabel,
}: {
  label: string;
  pendingLabel: string;
}) {
  const { pending } = useFormStatus();
  return (
    <Button
      type="submit"
      disabled={pending}
      className="h-12 rounded-full bg-white px-6 text-base font-medium text-neutral-950 hover:bg-neutral-200 disabled:opacity-60"
    >
      {pending ? pendingLabel : label}
    </Button>
  );
}

type SignupFormProps = {
  content: SignupContent;
  className?: string;
  onSuccess?: (position: number) => void;
};

export function SignupForm({ content, className, onSuccess }: SignupFormProps) {
  const focusedRef = useRef(false);
  const [state, formAction] = useActionState<SignupResult | null, FormData>(
    async (prev, formData) => {
      track("signup_attempted");
      const result = await signupAction(prev, formData);
      if (result.success) {
        track("signup_succeeded", { position: result.position });
        if (onSuccess) onSuccess(result.position);
      } else {
        track("signup_failed", { error: result.error });
      }
      return result;
    },
    null,
  );

  useEffect(() => {
    focusedRef.current = false;
  }, []);

  if (state?.success) {
    return (
      <div className={className}>
        <SignupSuccess position={state.position} content={content} />
      </div>
    );
  }

  return (
    <form
      action={formAction}
      className={cn("flex w-full max-w-md flex-col gap-3", className)}
    >
      {/* Honeypot — visually hidden but kept in the DOM. Bots fill it; humans don't. */}
      <div
        aria-hidden="true"
        style={{
          position: "absolute",
          left: "-9999px",
          width: 1,
          height: 1,
          overflow: "hidden",
        }}
      >
        <label htmlFor="signup-hp">Leave this field empty</label>
        <input
          id="signup-hp"
          name="hp"
          type="text"
          tabIndex={-1}
          autoComplete="off"
          defaultValue=""
        />
      </div>
      <div className="flex w-full flex-col gap-3 md:flex-row">
        <label htmlFor="signup-email" className="sr-only">
          Email address
        </label>
        <Input
          id="signup-email"
          name="email"
          type="email"
          required
          placeholder={content.email_placeholder}
          aria-invalid={state && !state.success ? true : undefined}
          onFocus={() => {
            if (!focusedRef.current) {
              focusedRef.current = true;
              track("signup_form_focused");
            }
          }}
          className="h-12 flex-1 rounded-full border-white/10 bg-white/5 px-5 text-base text-white placeholder:text-neutral-500 focus-visible:ring-2 focus-visible:ring-white/30"
        />
        <SubmitButton
          label={content.submit_label}
          pendingLabel={content.submit_pending_label}
        />
      </div>
      {state && !state.success ? (
        <p
          role="alert"
          className="px-2 text-left text-sm text-red-400 md:text-center"
        >
          {state.error}
        </p>
      ) : null}
    </form>
  );
}
