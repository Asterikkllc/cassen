"use server";

import { revalidatePath } from "next/cache";
import { getSupabaseServer } from "@/lib/supabase-server";
import { getSupabaseAdmin } from "@/lib/supabase";

export type UploadResult =
  | { ok: true; url: string }
  | { ok: false; error: string };

const MAX_BYTES = 5 * 1024 * 1024;
const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"] as const;
type AllowedType = (typeof ALLOWED_TYPES)[number];

async function requireAdmin() {
  const auth = await getSupabaseServer();
  const {
    data: { user },
  } = await auth.auth.getUser();
  const adminEmail = process.env.ADMIN_EMAIL?.toLowerCase();
  return Boolean(user && adminEmail && user.email?.toLowerCase() === adminEmail);
}

function sniffMime(bytes: Uint8Array): AllowedType | null {
  if (bytes.length >= 3 && bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff) {
    return "image/jpeg";
  }
  if (
    bytes.length >= 8 &&
    bytes[0] === 0x89 &&
    bytes[1] === 0x50 &&
    bytes[2] === 0x4e &&
    bytes[3] === 0x47 &&
    bytes[4] === 0x0d &&
    bytes[5] === 0x0a &&
    bytes[6] === 0x1a &&
    bytes[7] === 0x0a
  ) {
    return "image/png";
  }
  if (
    bytes.length >= 12 &&
    bytes[0] === 0x52 &&
    bytes[1] === 0x49 &&
    bytes[2] === 0x46 &&
    bytes[3] === 0x46 &&
    bytes[8] === 0x57 &&
    bytes[9] === 0x45 &&
    bytes[10] === 0x42 &&
    bytes[11] === 0x50
  ) {
    return "image/webp";
  }
  return null;
}

export async function uploadFounderPhoto(
  formData: FormData,
): Promise<UploadResult> {
  if (!(await requireAdmin())) {
    return { ok: false, error: "Forbidden" };
  }

  const file = formData.get("file");
  if (!(file instanceof File) || file.size === 0) {
    return { ok: false, error: "No file provided." };
  }
  if (file.size > MAX_BYTES) {
    return { ok: false, error: "File must be under 5 MB." };
  }
  if (!ALLOWED_TYPES.includes(file.type as AllowedType)) {
    return { ok: false, error: "Use JPG, PNG, or WebP." };
  }

  const head = new Uint8Array(await file.slice(0, 16).arrayBuffer());
  const sniffed = sniffMime(head);
  if (!sniffed || sniffed !== file.type) {
    return {
      ok: false,
      error: "File contents don't match the declared image type.",
    };
  }

  const admin = getSupabaseAdmin();
  const ext = sniffed === "image/png" ? "png" : sniffed === "image/webp" ? "webp" : "jpg";
  const rand = Math.random().toString(36).slice(2, 10);
  const path = `founder/${Date.now()}-${rand}.${ext}`;

  const { error: uploadError } = await admin.storage
    .from("public-assets")
    .upload(path, file, {
      contentType: sniffed,
      upsert: false,
    });

  if (uploadError) {
    console.error("[upload] storage error", uploadError);
    return {
      ok: false,
      error: "Upload failed. Make sure the public-assets bucket exists.",
    };
  }

  const { data } = admin.storage.from("public-assets").getPublicUrl(path);
  const url = data.publicUrl;

  revalidatePath("/");
  revalidatePath("/admin/content");
  return { ok: true, url };
}
