import { NextResponse } from "next/server";
import { getSupabaseAdmin } from "@/lib/supabase";
import { getSupabaseServer } from "@/lib/supabase-server";

function csvEscape(value: unknown): string {
  if (value === null || value === undefined) return "";
  const s = String(value);
  if (/[",\n\r]/.test(s)) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

export async function GET() {
  const authClient = await getSupabaseServer();
  const {
    data: { user },
  } = await authClient.auth.getUser();
  const adminEmail = process.env.ADMIN_EMAIL?.toLowerCase();
  if (!user || !adminEmail || user.email?.toLowerCase() !== adminEmail) {
    return new NextResponse("Forbidden", { status: 403 });
  }

  const admin = getSupabaseAdmin();
  const { data, error } = await admin
    .from("waitlist")
    .select("id, email, referrer, approved, created_at")
    .order("id", { ascending: true });

  if (error) {
    return new NextResponse("Failed to export.", { status: 500 });
  }

  const header = ["id", "email", "referrer", "approved", "created_at"];
  const rows = (data ?? []).map((r) =>
    [r.id, r.email, r.referrer, r.approved, r.created_at]
      .map(csvEscape)
      .join(","),
  );
  const csv = [header.join(","), ...rows].join("\n");

  return new NextResponse(csv, {
    status: 200,
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="cassen-waitlist-${new Date().toISOString().slice(0, 10)}.csv"`,
    },
  });
}
