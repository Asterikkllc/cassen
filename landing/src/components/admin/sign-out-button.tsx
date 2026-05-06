"use client";

import { useTransition } from "react";
import { createBrowserClient } from "@supabase/ssr";
import { Button } from "@/components/ui/button";

export function SignOutButton() {
  const [pending, startTransition] = useTransition();

  function onClick() {
    startTransition(async () => {
      const supabase = createBrowserClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      );
      await supabase.auth.signOut();
      window.location.href = "/admin/login";
    });
  }

  return (
    <Button
      onClick={onClick}
      disabled={pending}
      variant="ghost"
      className="text-neutral-300 hover:bg-neutral-900 hover:text-white"
    >
      {pending ? "Signing out…" : "Sign out"}
    </Button>
  );
}
