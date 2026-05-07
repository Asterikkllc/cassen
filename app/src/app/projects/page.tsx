import Link from "next/link";
import { Plus } from "lucide-react";
import { auth, currentUser } from "@clerk/nextjs/server";
import { SiteHeader } from "@/components/site-header";
import { listMyProjects } from "@/app/actions/projects";

export const metadata = { title: "Projects" };
export const dynamic = "force-dynamic";

const STATUS_LABEL: Record<string, string> = {
  draft: "Draft",
  planning: "Planning",
  designing: "Designing",
  simulating: "Simulating",
  sourcing: "Sourcing",
  fabricating: "Fabricating",
  assembled: "Assembled",
  shipped: "Shipped",
  archived: "Archived",
  failed: "Failed",
};

export default async function ProjectsPage() {
  await auth.protect();
  const user = await currentUser();
  const greeting =
    user?.firstName ?? user?.username ?? user?.emailAddresses[0]?.emailAddress;

  const projects = await listMyProjects();

  return (
    <>
      <SiteHeader />
      <main className="mx-auto w-full max-w-5xl px-6 py-16">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <div className="flex flex-col gap-3">
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-neutral-500">
              Projects
            </p>
            <h1 className="text-balance text-3xl font-semibold tracking-tight text-white md:text-4xl">
              {greeting ? `Welcome, ${greeting}.` : "Welcome."}
            </h1>
            <p className="text-pretty text-neutral-400">
              {projects.length === 0
                ? "Describe a product. The agent does the rest."
                : `You have ${projects.length} project${projects.length === 1 ? "" : "s"}.`}
            </p>
          </div>
          <Link
            href="/projects/new"
            className="inline-flex h-10 items-center justify-center rounded-full bg-white px-5 text-sm font-medium text-neutral-950 transition-colors hover:bg-neutral-200"
          >
            <Plus className="mr-1.5 h-4 w-4" />
            New project
          </Link>
        </div>

        {projects.length === 0 ? (
          <div className="mt-12 flex flex-col items-center gap-4 rounded-2xl border border-dashed border-neutral-800 bg-neutral-900/30 p-12 text-center">
            <p className="text-neutral-300">
              No projects yet. Start by describing what you want to build.
            </p>
            <Link
              href="/projects/new"
              className="inline-flex h-11 items-center justify-center rounded-full bg-white px-6 text-base font-medium text-neutral-950 transition-colors hover:bg-neutral-200"
            >
              Start your first project
            </Link>
          </div>
        ) : (
          <ul className="mt-10 grid grid-cols-1 gap-4 md:grid-cols-2">
            {projects.map((p) => (
              <li
                key={p.id}
                className="rounded-2xl border border-neutral-800 bg-neutral-900/40 transition-colors hover:border-neutral-700 hover:bg-neutral-900/70"
              >
                <Link href={`/projects/${p.id}`} className="block p-5">
                  <div className="flex items-start justify-between gap-3">
                    <h2 className="text-base font-medium text-white">
                      {p.title ?? "Untitled project"}
                    </h2>
                    <span className="shrink-0 rounded-full border border-neutral-800 bg-neutral-900 px-2.5 py-0.5 text-xs text-neutral-400">
                      {STATUS_LABEL[p.status] ?? p.status}
                    </span>
                  </div>
                  <p className="mt-3 line-clamp-3 text-sm text-neutral-400">
                    {p.prompt}
                  </p>
                  <p className="mt-4 text-xs text-neutral-600">
                    Created {new Date(p.created_at).toLocaleString()}
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </main>
    </>
  );
}
