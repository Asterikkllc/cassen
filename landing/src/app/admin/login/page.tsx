"use client";

import { useActionState } from "react";
import { useFormStatus } from "react-dom";
import {
  requestAdminMagicLink,
  type AdminLoginResult,
} from "@/app/actions/admin-login";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <Button
      type="submit"
      disabled={pending}
      className="h-11 bg-white text-neutral-950 hover:bg-neutral-200"
    >
      {pending ? "Sending…" : "Send magic link"}
    </Button>
  );
}

export default function AdminLoginPage() {
  const [state, formAction] = useActionState<
    AdminLoginResult | null,
    FormData
  >(async (prev, formData) => requestAdminMagicLink(prev, formData), null);

  return (
    <main className="flex min-h-screen items-center justify-center bg-neutral-950 px-6">
      <div className="w-full max-w-sm rounded-2xl border border-neutral-800 bg-neutral-900/40 p-8">
        <h1 className="text-2xl font-semibold tracking-tight text-white">
          Admin sign in
        </h1>
        <p className="mt-2 text-sm text-neutral-400">
          Enter your email to receive a magic link.
        </p>

        {state?.ok ? (
          <p className="mt-6 rounded-lg border border-emerald-700/30 bg-emerald-500/10 p-4 text-sm text-emerald-300">
            If that email is registered, a magic link is on its way. Check your
            inbox.
          </p>
        ) : (
          <form action={formAction} className="mt-6 flex flex-col gap-3">
            <label htmlFor="admin-email" className="sr-only">
              Email
            </label>
            <Input
              id="admin-email"
              name="email"
              type="email"
              required
              placeholder="you@cassen.ai"
              className="h-11 border-white/10 bg-white/5 text-white placeholder:text-neutral-500"
            />
            <SubmitButton />
          </form>
        )}
      </div>
    </main>
  );
}
