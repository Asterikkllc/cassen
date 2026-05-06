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
  created_at: string;
  updated_at: string;
};
