import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Trash2 } from "lucide-react";
import { ProjectShell } from "@/components/project-shell";
import type { ChatMessage as UiChatMessage } from "@/components/chat-thread";
import {
  deleteProjectFromForm,
  getMyProject,
  listProjectMessages,
} from "@/app/actions/projects";

export const dynamic = "force-dynamic";

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
  const { id } = await params;
  const project = await getMyProject(id);
  if (!project) notFound();

  const persisted = await listProjectMessages(project.id);

  // Map persisted DB rows → UI shape used by ChatThread.
  const seededMessages: UiChatMessage[] = persisted.length === 0
    ? [
        {
          id: "seed-prompt",
          role: "user",
          content: project.prompt,
          createdAt: project.created_at,
        },
      ]
    : persisted.map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        thinking: m.thinking,
        toolCalls: m.tool_calls,
        createdAt: m.created_at,
      }));

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex h-12 items-center justify-between gap-3 border-b border-border bg-background/80 px-4 backdrop-blur">
        <div className="flex min-w-0 items-center gap-3">
          <Link
            href="/projects"
            className="flex flex-shrink-0 items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">All projects</span>
          </Link>
          <span className="hidden h-3 w-px bg-border sm:inline-block" />
          <h1 className="min-w-0 truncate text-sm font-semibold sm:text-base">
            {project.title ?? "Untitled project"}
          </h1>
        </div>
        <form action={deleteProjectFromForm}>
          <input type="hidden" name="project_id" value={project.id} />
          <button
            type="submit"
            className="flex h-8 items-center gap-1.5 rounded-md px-2 text-xs text-destructive hover:bg-destructive/10"
          >
            <Trash2 className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Delete</span>
          </button>
        </form>
      </div>
      <div className="flex-1 overflow-hidden">
        <ProjectShell
          projectId={project.id}
          projectTitle={project.title}
          initialMessages={seededMessages}
        />
      </div>
    </div>
  );
}
