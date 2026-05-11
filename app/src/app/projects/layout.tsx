import { cookies } from "next/headers";
import { auth } from "@clerk/nextjs/server";
import {
  ProjectsSidebar,
  type SidebarProject,
} from "@/components/projects-sidebar";
import { getSupabaseAdmin } from "@/lib/supabase";

const COLLAPSE_COOKIE = "cassen_sb_collapsed";

/**
 * Nested layout for every page under `/projects/*`. Mounts the
 * persistent collapsible sidebar on the left and renders the page
 * in the remaining column. Sidebar collapse state is read from a
 * cookie so SSR matches the user's last preference.
 */
export default async function ProjectsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { userId } = await auth();
  const collapsedRaw = (await cookies()).get(COLLAPSE_COOKIE)?.value;
  const initialCollapsed = collapsedRaw === "1";

  let projects: SidebarProject[] = [];
  if (userId) {
    const admin = getSupabaseAdmin();
    const { data, error } = await admin
      .from("projects")
      .select("id, title, prompt, status, created_at")
      .eq("owner_id", userId)
      .order("created_at", { ascending: false })
      .limit(60);
    if (error) {
      console.error("[projects-layout] supabase error", error);
    } else if (data) {
      projects = data as SidebarProject[];
    }
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <ProjectsSidebar
        projects={projects}
        initialCollapsed={initialCollapsed}
      />
      <main className="flex h-screen flex-1 flex-col overflow-hidden">
        {children}
      </main>
    </div>
  );
}
