"use server";

import { z } from "zod";
import { revalidatePath } from "next/cache";
import { getSupabaseServer } from "@/lib/supabase-server";
import { getSupabaseAdmin } from "@/lib/supabase";
import type { SectionKey, SiteContent } from "@/lib/content/types";

export type SaveResult =
  | { ok: true }
  | { ok: false; error: string };

const SAFE_LINK_SCHEME = /^(https?:\/\/|mailto:|#|\/[^/])/i;
const safeLinkUrl = (max: number) =>
  z
    .string()
    .trim()
    .max(max)
    .refine(
      (v) => v === "" || v === "#" || SAFE_LINK_SCHEME.test(v),
      { message: "URL must use http(s), mailto:, an anchor (#…), or a same-site path (/…)." },
    );

const safeEmail = (max: number) =>
  z
    .string()
    .trim()
    .max(max)
    .refine((v) => v === "" || z.string().email().safeParse(v).success, {
      message: "Must be a valid email address.",
    });

const HeroSchema = z.object({
  badge: z.string().trim().max(120),
  headline: z.string().trim().min(1).max(280),
  subheadline: z.string().trim().min(1).max(600),
  trust_line: z.string().trim().max(200),
});

const supabaseStoragePrefix = (() => {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  return url ? `${url.replace(/\/$/, "")}/storage/v1/object/public/` : null;
})();

const FounderSchema = z.object({
  eyebrow: z.string().trim().max(120),
  heading: z.string().trim().min(1).max(280),
  paragraphs: z.array(z.string().trim().max(2000)).min(1).max(6),
  photo_url: z
    .string()
    .trim()
    .url()
    .max(800)
    .refine(
      (v) => !supabaseStoragePrefix || v.startsWith(supabaseStoragePrefix),
      { message: "Photo URL must come from this project's Supabase Storage." },
    )
    .or(z.literal(""))
    .nullable(),
  photo_alt: z.string().trim().max(200),
  vision_memo_url: safeLinkUrl(500),
  read_more_label: z.string().trim().min(1).max(80),
  initials: z.string().trim().min(1).max(4),
});

const HowItWorksSchema = z.object({
  eyebrow: z.string().trim().max(120),
  headline: z.string().trim().min(1).max(280),
  subhead: z.string().trim().max(400),
  steps: z
    .array(
      z.object({
        number: z.string().trim().max(8),
        icon: z.string().trim().max(40),
        title: z.string().trim().min(1).max(120),
        body: z.string().trim().min(1).max(600),
      }),
    )
    .min(1)
    .max(8),
});

const UseCasesSchema = z.object({
  eyebrow: z.string().trim().max(120),
  headline: z.string().trim().min(1).max(280),
  subhead: z.string().trim().max(400),
  items: z
    .array(
      z.object({
        icon: z.string().trim().max(40),
        title: z.string().trim().min(1).max(120),
        body: z.string().trim().min(1).max(400),
      }),
    )
    .min(1)
    .max(12),
});

const FaqSchema = z.object({
  eyebrow: z.string().trim().max(120),
  headline: z.string().trim().min(1).max(280),
  items: z
    .array(
      z.object({
        q: z.string().trim().min(1).max(280),
        a: z.string().trim().min(1).max(2000),
      }),
    )
    .min(1)
    .max(20),
});

const CtaSchema = z.object({
  headline: z.string().trim().min(1).max(280),
  subheadline: z.string().trim().max(400),
  trust_line: z.string().trim().max(200),
});

const FooterSchema = z.object({
  wordmark: z.string().trim().min(1).max(60),
  tagline: z.string().trim().max(120),
  vision_url: safeLinkUrl(500),
  vision_label: z.string().trim().max(80),
  contact_email: safeEmail(254),
  contact_label: z.string().trim().max(80),
  twitter_url: safeLinkUrl(500),
  twitter_label: z.string().trim().max(80),
  copyright_template: z.string().trim().min(1).max(200),
});

const SignupSchema = z.object({
  email_placeholder: z.string().trim().min(1).max(120),
  submit_label: z.string().trim().min(1).max(60),
  submit_pending_label: z.string().trim().min(1).max(60),
  success_heading: z.string().trim().min(1).max(120),
  success_position_template: z.string().trim().min(1).max(200),
  success_body: z.string().trim().min(1).max(600),
  share_label: z.string().trim().min(1).max(120),
  share_text: z.string().trim().min(1).max(280),
  error_invalid_email: z.string().trim().min(1).max(200),
  error_duplicate: z.string().trim().min(1).max(200),
  error_generic: z.string().trim().min(1).max(200),
  error_not_configured: z.string().trim().min(1).max(200),
});

const WelcomeEmailSchema = z.object({
  subject: z.string().trim().min(1).max(140),
  greeting: z.string().trim().min(1).max(120),
  position_line_template: z.string().trim().min(1).max(400),
  body_paragraphs: z.array(z.string().trim().min(1).max(2000)).min(1).max(8),
  signature: z.string().trim().min(1).max(200),
  footer_disclaimer: z.string().trim().min(1).max(500),
});

const MetaSchema = z.object({
  title: z.string().trim().min(1).max(200),
  description: z.string().trim().min(1).max(400),
});

const SECTION_SCHEMAS = {
  hero: HeroSchema,
  founder: FounderSchema,
  how_it_works: HowItWorksSchema,
  use_cases: UseCasesSchema,
  faq: FaqSchema,
  cta: CtaSchema,
  footer: FooterSchema,
  signup: SignupSchema,
  welcome_email: WelcomeEmailSchema,
  meta: MetaSchema,
} as const;

async function requireAdmin(): Promise<{ ok: true } | { ok: false; error: string }> {
  const auth = await getSupabaseServer();
  const {
    data: { user },
  } = await auth.auth.getUser();
  const adminEmail = process.env.ADMIN_EMAIL?.toLowerCase();
  if (!user || !adminEmail || user.email?.toLowerCase() !== adminEmail) {
    return { ok: false, error: "Forbidden" };
  }
  return { ok: true };
}

export async function saveSectionAction<K extends SectionKey>(
  key: K,
  value: SiteContent[K],
): Promise<SaveResult> {
  const auth = await requireAdmin();
  if (!auth.ok) return auth;

  const schema = SECTION_SCHEMAS[key];
  const parsed = schema.safeParse(value);
  if (!parsed.success) {
    return {
      ok: false,
      error: parsed.error.issues[0]?.message ?? "Validation failed.",
    };
  }

  const admin = getSupabaseAdmin();
  const { error } = await admin
    .from("site_content")
    .upsert({ key, value: parsed.data }, { onConflict: "key" });

  if (error) {
    console.error("[content] save error", error);
    return { ok: false, error: "Save failed." };
  }

  revalidatePath("/");
  revalidatePath("/admin/content");
  return { ok: true };
}
