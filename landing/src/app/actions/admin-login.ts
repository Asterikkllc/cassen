"use server";

import { z } from "zod";
import { headers } from "next/headers";
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { checkRateLimit, getClientIp } from "@/lib/rate-limit";

const Schema = z.object({
  email: z.string().trim().toLowerCase().email(),
});

export type AdminLoginResult = { ok: boolean };

export async function requestAdminMagicLink(
  _prev: AdminLoginResult | null,
  formData: FormData,
): Promise<AdminLoginResult> {
  const parsed = Schema.safeParse({ email: formData.get("email") });

  // Always return ok: true so the UI never reveals whether the email matched
  // the admin or whether Supabase accepted it. This prevents email enumeration.
  if (!parsed.success) return { ok: true };

  const h = await headers();
  const ip = getClientIp(h);
  const rl = await checkRateLimit("admin_login_ip", ip);
  if (!rl.ok) {
    console.warn("[admin-login] rate limited", { ip });
    return { ok: true };
  }

  const submitted = parsed.data.email;
  const adminEmail = process.env.ADMIN_EMAIL?.trim().toLowerCase();

  // Silently no-op if the submitted address isn't the admin's. The user
  // sees the same "check your inbox" UI either way.
  if (!adminEmail || submitted !== adminEmail) {
    return { ok: true };
  }

  const cookieStore = await cookies();
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            for (const { name, value, options } of cookiesToSet) {
              cookieStore.set(name, value, options);
            }
          } catch {
            // Server-component cookie set is a no-op here; safe to ignore.
          }
        },
      },
    },
  );

  const origin =
    h.get("origin") ??
    `${h.get("x-forwarded-proto") ?? "http"}://${h.get("host") ?? "localhost:3000"}`;

  await supabase.auth.signInWithOtp({
    email: submitted,
    options: {
      emailRedirectTo: `${origin}/auth/callback`,
      shouldCreateUser: false,
    },
  });

  return { ok: true };
}
