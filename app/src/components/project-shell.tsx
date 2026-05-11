"use client";

import { useState } from "react";
import {
  Box,
  ChevronLeft,
  FlaskConical,
  ListChecks,
  PanelRightOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ChatThread, type ChatMessage } from "@/components/chat-thread";

export type ArtifactTab = "workshop" | "test-room" | "specs";

export type ProjectShellProps = {
  projectId: string;
  projectTitle: string | null;
  initialMessages: ChatMessage[];
};

const TABS: { id: ArtifactTab; label: string; icon: typeof Box }[] = [
  { id: "workshop", label: "Workshop", icon: Box },
  { id: "test-room", label: "Test Room", icon: FlaskConical },
  { id: "specs", label: "Specs", icon: ListChecks },
];

/**
 * Top-level project layout — chat on the left, artifact panel on the
 * right (desktop) / drawer (mobile). Three artifact tabs:
 *
 *   - **Workshop** (PRD §5.3) — photoreal live-assembly 3D view.
 *     Slice 0 ships a placeholder; the WebGPU PBR / Omniverse hybrid
 *     pipeline lands in a later slice.
 *   - **Test Room** (PRD §5.4) — physics sandbox with environmental
 *     controls. Slice 0 placeholder.
 *   - **Specs** — BoM, sourced parts, materials breakdown, sim
 *     summary. Slice 0 placeholder.
 */
export function ProjectShell({
  projectId,
  projectTitle,
  initialMessages,
}: ProjectShellProps) {
  const [tab, setTab] = useState<ArtifactTab>("workshop");
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <div className="flex h-full w-full overflow-hidden">
      {/* Chat */}
      <div className="flex h-full flex-1 flex-col border-r border-border lg:w-1/2 lg:flex-none">
        <ChatThread projectId={projectId} initialMessages={initialMessages} />
      </div>

      {/* Desktop artifact pane */}
      <div className="hidden h-full flex-col lg:flex lg:w-1/2 lg:flex-none">
        <ArtifactPanel tab={tab} onTabChange={setTab} title={projectTitle} />
      </div>

      {/* Mobile floating toggle */}
      <button
        type="button"
        onClick={() => setDrawerOpen(true)}
        className="fixed bottom-20 right-4 z-30 flex items-center gap-2 rounded-full border border-primary/40 bg-background/85 px-4 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-primary shadow-[0_0_18px_oklch(0.78_0.17_200/0.3)] backdrop-blur lg:hidden"
      >
        <PanelRightOpen className="h-3.5 w-3.5" />
        View design
      </button>

      {/* Mobile drawer */}
      {drawerOpen ? (
        <div className="fixed inset-0 z-40 bg-black/70 lg:hidden">
          <div className="absolute inset-x-0 bottom-0 top-12 overflow-hidden rounded-t-2xl border-t border-border bg-background">
            <div className="flex items-center justify-between border-b border-border px-4 py-2">
              <button
                type="button"
                onClick={() => setDrawerOpen(false)}
                className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
              >
                <ChevronLeft className="h-4 w-4" />
                Back
              </button>
            </div>
            <ArtifactPanel
              tab={tab}
              onTabChange={setTab}
              title={projectTitle}
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}

function ArtifactPanel({
  tab,
  onTabChange,
  title,
}: {
  tab: ArtifactTab;
  onTabChange: (t: ArtifactTab) => void;
  title: string | null;
}) {
  return (
    <div className="flex h-full flex-col bg-background/60">
      {/* Tab bar */}
      <div className="flex items-center justify-between border-b border-border px-4">
        <div className="flex">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              onClick={() => onTabChange(id)}
              className={cn(
                "relative flex items-center gap-1.5 px-3 py-3 text-sm transition-colors",
                tab === id
                  ? "text-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              <Icon className="h-3.5 w-3.5" />
              {label}
              {tab === id ? (
                <span className="absolute inset-x-3 bottom-0 h-0.5 rounded-t-sm bg-primary" />
              ) : null}
            </button>
          ))}
        </div>
        <p className="hidden truncate font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground sm:block">
          {title ? title.slice(0, 40) : "Untitled project"}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        {tab === "workshop" ? <WorkshopPlaceholder /> : null}
        {tab === "test-room" ? <TestRoomPlaceholder /> : null}
        {tab === "specs" ? <SpecsPlaceholder /> : null}
      </div>
    </div>
  );
}

function WorkshopPlaceholder() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 px-6 py-12 text-center">
      <Box className="h-10 w-10 text-primary/60" />
      <div className="flex flex-col gap-2">
        <p className="text-sm font-medium">Workshop</p>
        <p className="max-w-sm text-pretty text-xs text-muted-foreground">
          Photoreal live-assembly view of your product. Real CAD, real
          materials, real lighting. Lands once the agent service emits its
          first design pass.
        </p>
      </div>
      <span className="rounded-full border border-border bg-card/60 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
        Coming soon
      </span>
    </div>
  );
}

function TestRoomPlaceholder() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 px-6 py-12 text-center">
      <FlaskConical className="h-10 w-10 text-primary/60" />
      <div className="flex flex-col gap-2">
        <p className="text-sm font-medium">Test Room</p>
        <p className="max-w-sm text-pretty text-xs text-muted-foreground">
          Physics sandbox. Configure environmental conditions (wind,
          friction, gravity, lighting, interference) and watch your product
          behave under real physics.
        </p>
      </div>
      <span className="rounded-full border border-border bg-card/60 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
        Coming soon
      </span>
    </div>
  );
}

function SpecsPlaceholder() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 px-6 py-12 text-center">
      <ListChecks className="h-10 w-10 text-primary/60" />
      <div className="flex flex-col gap-2">
        <p className="text-sm font-medium">Specs</p>
        <p className="max-w-sm text-pretty text-xs text-muted-foreground">
          Bill of materials with live pricing, materials breakdown,
          simulation summary, and order checkout. Populates as the agent
          completes design passes.
        </p>
      </div>
      <span className="rounded-full border border-border bg-card/60 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
        Coming soon
      </span>
    </div>
  );
}
