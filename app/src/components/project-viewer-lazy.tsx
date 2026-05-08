"use client";

import dynamic from "next/dynamic";
import type { CandidatePart } from "@/components/project-viewer";

const ProjectViewer = dynamic(
  () => import("@/components/project-viewer").then((m) => m.ProjectViewer),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-[440px] w-full items-center justify-center rounded-2xl border border-neutral-800 bg-neutral-950 text-sm text-neutral-500">
        Loading viewer…
      </div>
    ),
  },
);

export function ProjectViewerLazy({
  candidateParts,
  glbBase64,
}: {
  candidateParts: CandidatePart[];
  glbBase64?: string;
}) {
  return (
    <ProjectViewer candidateParts={candidateParts} glbBase64={glbBase64} />
  );
}
