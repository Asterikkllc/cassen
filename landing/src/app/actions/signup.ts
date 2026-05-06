"use server";

import { z } from "zod";
import { headers } from "next/headers";
import { getSupabaseAdmin } from "@/lib/supabase";
import { sendWelcomeEmail } from "@/lib/mailer";
import { getSiteContent } from "@/lib/content/server";
import { checkRateLimit, getClientIp } from "@/lib/rate-limit";

const SignupSchema = z.object({
  email: z.string().trim().toLowerCase().email(),
  referrer: z.string().optional(),
  hp: z.string().max(0).optional(),
});

export type SignupResult =
  | { success: true; position: number }
  | { success: false; error: string };

export async function signupAction(
  _prevState: SignupResult | null,
  formData: FormData,
): Promise<SignupResult> {
  const rawEmail = formData.get("email");
  const hp = formData.get("hp");
  console.log("[signup] received submission", { rawEmail });

  const content = await getSiteContent();
  const errs = content.signup;

  if (typeof hp === "string" && hp.length > 0) {
    console.warn("[signup] honeypot tripped, ignoring submission");
    return { success: true, position: 0 };
  }

  const parsed = SignupSchema.safeParse({
    email: rawEmail,
    referrer: formData.get("referrer") ?? undefined,
    hp: typeof hp === "string" ? hp : undefined,
  });

  if (!parsed.success) {
    console.log("[signup] validation failed");
    return { success: false, error: errs.error_invalid_email };
  }

  const { email, referrer } = parsed.data;
  console.log("[signup] validated", { email });

  const h = await headers();
  const ip = getClientIp(h);
  const rl = await checkRateLimit("signup_ip", ip);
  if (!rl.ok) {
    console.warn("[signup] rate limited", { ip, retryAfterMs: rl.retryAfterMs });
    return { success: false, error: errs.error_generic };
  }

  let supabase;
  try {
    supabase = getSupabaseAdmin();
  } catch {
    console.error("[signup] supabase admin client missing env");
    return { success: false, error: errs.error_not_configured };
  }

  const { data, error } = await supabase
    .from("waitlist")
    .insert({ email, referrer: referrer ?? null })
    .select("id")
    .single();

  if (error) {
    if (error.code === "23505") {
      console.log("[signup] duplicate email, no welcome will be sent");
      return { success: false, error: errs.error_duplicate };
    }
    console.error("[signup] supabase insert error", error);
    return { success: false, error: errs.error_generic };
  }

  const position = Number(data.id);
  console.log("[signup] inserted", { email, position });

  const start = Date.now();
  try {
    const result = await sendWelcomeEmail(email, position);
    if (result.sent) {
      console.log("[signup] welcome email sent", {
        email,
        ms: Date.now() - start,
      });
    } else {
      console.warn("[signup] welcome email skipped:", result.reason);
    }
  } catch (err) {
    console.error("[signup] welcome email failed", err);
  }

  return { success: true, position };
}
