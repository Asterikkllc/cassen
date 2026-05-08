import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Trash2 } from "lucide-react";
import { auth } from "@clerk/nextjs/server";
import { SiteHeader } from "@/components/site-header";
import { AgentRun } from "@/components/agent-run";
import { ProjectViewerLazy } from "@/components/project-viewer-lazy";
import { Button } from "@/components/ui/button";
import {
  deleteProjectFromForm,
  getLatestSnapshot,
  getMyProject,
} from "@/app/actions/projects";
import type { CandidatePart } from "@/components/project-viewer";
import type { NodeSnapshot, ToolCall } from "@/components/agent-run";

export const dynamic = "force-dynamic";

const STATUS_LABEL: Record<string, string> = {
  draft: "Draft",
  planning: "Planning",
  researching: "Researching",
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

function extractCandidateParts(
  snapshot: Record<string, unknown> | undefined,
): CandidatePart[] {
  if (!snapshot) return [];
  const research = (snapshot.research as Record<string, unknown> | undefined) ?? {};
  const electronics = (research.electronics as Record<string, unknown> | undefined) ?? {};
  const raw = electronics.candidate_parts;
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((p): p is Record<string, unknown> => p !== null && typeof p === "object")
    .map((p) => ({
      function: typeof p.function === "string" ? p.function : undefined,
      mpn: typeof p.mpn === "string" ? p.mpn : undefined,
      rationale: typeof p.rationale === "string" ? p.rationale : undefined,
    }))
    .filter((p) => p.mpn);
}

function extractGlbBase64(
  snapshot: Record<string, unknown> | undefined,
): string | undefined {
  if (!snapshot) return undefined;
  const research = (snapshot.research as Record<string, unknown> | undefined) ?? {};
  const mechanical =
    (research.mechanical as Record<string, unknown> | undefined) ?? {};
  const glb = mechanical.glb_b64;
  return typeof glb === "string" && glb.length > 0 ? glb : undefined;
}

function callsFromResearch(raw: unknown): ToolCall[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((c): c is Record<string, unknown> => c !== null && typeof c === "object")
    .map((c) => ({
      id: typeof c.id === "string" ? c.id : crypto.randomUUID(),
      name: typeof c.name === "string" ? c.name : "tool",
      input: c.input,
      output_text:
        typeof c.output_text === "string" ? c.output_text : undefined,
      is_error: c.is_error === true,
      error: typeof c.error === "string" ? c.error : undefined,
      status: c.is_error === true ? "error" : c.error ? "error" : "done",
    }));
}

function nodeFromResearch(
  nodeName: string,
  raw: unknown,
): NodeSnapshot | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const r = raw as Record<string, unknown>;
  const text = typeof r.final_text === "string" ? r.final_text : "";
  const toolCalls = callsFromResearch(r.calls);
  if (!text && toolCalls.length === 0) return undefined;
  return { node: nodeName, text, toolCalls, done: true };
}

function extractNodes(
  snapshot: Record<string, unknown> | undefined,
): NodeSnapshot[] {
  if (!snapshot) return [];
  const out: NodeSnapshot[] = [];

  const plannerText =
    typeof snapshot.planner_output === "string" ? snapshot.planner_output : "";
  if (plannerText) {
    out.push({ node: "planner", text: plannerText, toolCalls: [], done: true });
  }

  const research =
    (snapshot.research as Record<string, unknown> | undefined) ?? {};

  const elec = nodeFromResearch("electronics_research", research.electronics);
  if (elec) out.push(elec);

  const mechHw = nodeFromResearch(
    "mechanical_research",
    research.mechanical_research,
  );
  if (mechHw) out.push(mechHw);

  const mechDesign = nodeFromResearch("mechanical_design", research.mechanical);
  if (mechDesign) out.push(mechDesign);

  const fluids = nodeFromResearch("fluids_research", research.fluids);
  if (fluids) out.push(fluids);

  const designerText =
    typeof snapshot.designer_output === "string"
      ? snapshot.designer_output
      : "";
  if (designerText) {
    out.push({
      node: "designer",
      text: designerText,
      toolCalls: [],
      done: true,
    });
  }

  return out;
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

  const snapshot = await getLatestSnapshot(project.id);
  const candidateParts = extractCandidateParts(snapshot?.snapshot);
  const glbBase64 = extractGlbBase64(snapshot?.snapshot);
  const initialNodes = extractNodes(snapshot?.snapshot);
  // Debug: surface what's coming back from the DB for this project so
  // viewer-vs-snapshot mismatches are visible in next dev's terminal.
  console.log(
    `[project-detail] project=${project.id} snapshot_id=${snapshot?.id ?? "none"} ` +
      `candidate_parts=${candidateParts.length} ` +
      `glb_b64=${glbBase64 ? `present (${glbBase64.length} chars)` : "absent"} ` +
      `nodes=${initialNodes.length} ` +
      `created_at=${snapshot?.created_at ?? "n/a"}`,
  );

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
            <AgentRun
              projectId={project.id}
              initialNodes={initialNodes}
            />
          </div>
        </section>

        <section className="mt-6">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-xs font-medium uppercase tracking-wider text-neutral-500">
              3D Viewer
            </p>
            {candidateParts.length > 0 ? (
              <p className="text-xs text-neutral-600">
                Placeholder geometry — real STEP→GLTF lands in Phase 7b
              </p>
            ) : null}
          </div>
          <ProjectViewerLazy
            candidateParts={candidateParts}
            glbBase64={glbBase64}
          />
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
