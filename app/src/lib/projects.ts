import "server-only";

/** Status enum kept in lockstep with `projects_status_chk` in db/migrations/001_init.sql. */
export type ProjectStatus =
  | "draft"
  | "planning"
  | "designing"
  | "simulating"
  | "sourcing"
  | "fabricating"
  | "assembled"
  | "shipped"
  | "archived"
  | "failed";

export type Project = {
  id: string;
  owner_id: string;
  title: string | null;
  prompt: string;
  status: ProjectStatus;
  metadata: Record<string, unknown> | null;
  auto_mode: boolean;
  created_at: string;
  updated_at: string;
};

export type ChatMessageRole = "user" | "assistant" | "system";

export type ChatMessage = {
  id: string;
  project_id: string;
  role: ChatMessageRole;
  content: string;
  thinking: string | null;
  tool_calls: unknown;
  artifacts: unknown;
  created_at: string;
};
