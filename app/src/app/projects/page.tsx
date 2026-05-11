import Link from "next/link";
import { Plus, Sparkles } from "lucide-react";
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

export default async function ProjectsIndexPage() {
  const projects = await listMyProjects();

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto w-full max-w-5xl px-6 py-12">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <div className="flex flex-col gap-3">
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">
              Projects
            </p>
            <h1 className="text-balance text-3xl font-semibold tracking-tight md:text-4xl">
              {projects.length === 0
                ? "What do you want to build?"
                : `You have ${projects.length} project${projects.length === 1 ? "" : "s"}.`}
            </h1>
            <p className="max-w-xl text-pretty text-muted-foreground">
              {projects.length === 0
                ? "Describe a physical product in plain language. Cassen handles the rest — design, simulation, sourcing, fabrication."
                : "Open one to keep working, or start something new."}
            </p>
          </div>
          <Link
            href="/projects/new"
            className="inline-flex h-10 items-center justify-center gap-1.5 rounded-full bg-primary px-5 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90"
          >
            <Plus className="h-4 w-4" />
            New project
          </Link>
        </div>

        {projects.length === 0 ? (
          <Link
            href="/projects/new"
            className="mt-12 flex flex-col items-center gap-4 rounded-2xl border border-dashed border-border bg-card/30 p-12 text-center transition-colors hover:border-primary/50 hover:bg-card/60"
          >
            <Sparkles className="h-6 w-6 text-primary" />
            <p className="text-base">Start your first project</p>
            <p className="max-w-md text-sm text-muted-foreground">
              One paragraph is plenty. The agent decides what to ask back.
            </p>
          </Link>
        ) : (
          <ul className="mt-10 grid grid-cols-1 gap-4 md:grid-cols-2">
            {projects.map((p) => (
              <li
                key={p.id}
                className="rounded-2xl border border-border bg-card/40 transition-colors hover:border-primary/30 hover:bg-card/70"
              >
                <Link href={`/projects/${p.id}`} className="block p-5">
                  <div className="flex items-start justify-between gap-3">
                    <h2 className="text-base font-medium">
                      {p.title ?? "Untitled project"}
                    </h2>
                    <span className="shrink-0 rounded-full border border-border bg-card/40 px-2.5 py-0.5 text-xs text-muted-foreground">
                      {STATUS_LABEL[p.status] ?? p.status}
                    </span>
                  </div>
                  <p className="mt-3 line-clamp-3 text-sm text-muted-foreground">
                    {p.prompt}
                  </p>
                  <p className="mt-4 text-xs text-muted-foreground/70">
                    Created {new Date(p.created_at).toLocaleString()}
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
