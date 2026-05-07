import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Trash2 } from "lucide-react";
import { auth } from "@clerk/nextjs/server";
import { SiteHeader } from "@/components/site-header";
import { AgentRun } from "@/components/agent-run";
import { Button } from "@/components/ui/button";
import {
  deleteProjectFromForm,
  getMyProject,
} from "@/app/actions/projects";

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

type Params = Promise<{ id: string }>;

export async function generateMetadata({ params }: { params: Params }) {
  const { id } = await params;
  const project = await getMyProject(id);
  return { title: project?.title ?? "Project" };
}

export default async function ProjectDetailPage({
  params,
}: {
  params: Params;
}) {
  await auth.protect();
  const { id } = await params;
  const project = await getMyProject(id);
  if (!project) notFound();

  return (
    <>
      <SiteHeader />
      <main className="mx-auto w-full max-w-3xl px-6 py-12">
        <Link
          href="/projects"
          className="inline-flex items-center gap-2 text-sm text-neutral-400 transition-colors hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          All projects
        </Link>

        <div className="mt-8 flex flex-col gap-3">
          <div className="flex items-center gap-3">
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-neutral-500">
              Project
            </p>
            <span className="rounded-full border border-neutral-800 bg-neutral-900 px-2.5 py-0.5 text-xs text-neutral-400">
              {STATUS_LABEL[project.status] ?? project.status}
            </span>
          </div>
          <h1 className="text-balance text-3xl font-semibold tracking-tight text-white md:text-4xl">
            {project.title ?? "Untitled project"}
          </h1>
        </div>

        <section className="mt-10 rounded-2xl border border-neutral-800 bg-neutral-900/40 p-6">
          <p className="text-xs font-medium uppercase tracking-wider text-neutral-500">
            Prompt
          </p>
          <p className="mt-3 whitespace-pre-wrap text-base leading-relaxed text-neutral-200">
            {project.prompt}
          </p>
        </section>

        <section className="mt-6 rounded-2xl border border-neutral-800 bg-neutral-900/20 p-6">
          <p className="text-xs font-medium uppercase tracking-wider text-neutral-500">
            Agent run
          </p>
          <div className="mt-4">
            <AgentRun projectId={project.id} />
          </div>
        </section>

        <section className="mt-10 flex items-center justify-between gap-3 border-t border-neutral-900 pt-6 text-xs text-neutral-500">
          <span>Created {new Date(project.created_at).toLocaleString()}</span>
          <form action={deleteProjectFromForm}>
            <input type="hidden" name="project_id" value={project.id} />
            <Button
              type="submit"
              variant="ghost"
              className="text-red-400 hover:bg-red-950/30 hover:text-red-300"
            >
              <Trash2 className="mr-1.5 h-4 w-4" />
              Delete
            </Button>
          </form>
        </section>
      </main>
    </>
  );
}
