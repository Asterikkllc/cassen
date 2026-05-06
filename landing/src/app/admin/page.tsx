import Link from "next/link";
import { getSupabaseAdmin } from "@/lib/supabase";
import { ExportCsvButton } from "@/components/admin/export-csv-button";
import { SignOutButton } from "@/components/admin/sign-out-button";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Row = {
  id: number;
  email: string;
  referrer: string | null;
  approved: boolean;
  created_at: string;
};

export default async function AdminPage() {
  const supabase = getSupabaseAdmin();

  const { count, error: countError } = await supabase
    .from("waitlist")
    .select("id", { count: "exact", head: true });

  const { data: rows, error: rowsError } = await supabase
    .from("waitlist")
    .select("id, email, referrer, approved, created_at")
    .order("id", { ascending: false })
    .limit(50)
    .returns<Row[]>();

  return (
    <main className="min-h-screen bg-neutral-950 px-6 py-12 text-neutral-100">
      <div className="mx-auto max-w-5xl">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-white">
              Waitlist
            </h1>
            <p className="mt-2 text-sm text-neutral-400">
              {countError
                ? "Failed to load count."
                : `Total signups: ${count ?? 0}`}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/admin/content"
              className={cn(
                buttonVariants({ variant: "outline" }),
                "h-9 px-4 border-neutral-800 bg-neutral-900/50 text-neutral-100 hover:bg-neutral-800 hover:text-white",
              )}
            >
              Edit content
            </Link>
            <ExportCsvButton />
            <SignOutButton />
          </div>
        </div>

        <div className="mt-8 overflow-hidden rounded-2xl border border-neutral-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-neutral-900/50 text-xs uppercase tracking-wider text-neutral-400">
              <tr>
                <th className="px-4 py-3">#</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Referrer</th>
                <th className="px-4 py-3">Approved</th>
                <th className="px-4 py-3">Joined</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800">
              {rowsError ? (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-red-400">
                    Failed to load rows.
                  </td>
                </tr>
              ) : rows && rows.length > 0 ? (
                rows.map((row) => (
                  <tr key={row.id} className="hover:bg-neutral-900/30">
                    <td className="px-4 py-3 font-mono text-neutral-400">
                      {row.id}
                    </td>
                    <td className="px-4 py-3 text-white">{row.email}</td>
                    <td className="px-4 py-3 text-neutral-400">
                      {row.referrer ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-neutral-400">
                      {row.approved ? "yes" : "no"}
                    </td>
                    <td className="px-4 py-3 text-neutral-400">
                      {new Date(row.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-neutral-500">
                    No signups yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}
