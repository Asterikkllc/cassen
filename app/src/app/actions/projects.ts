"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { auth } from "@clerk/nextjs/server";
import { z } from "zod";
import { getSupabaseAdmin } from "@/lib/supabase";
import type { ChatMessage, Project } from "@/lib/projects";

// ---------------------------------------------------------------------------
// Reads
// ---------------------------------------------------------------------------

export async function listMyProjects(limit = 60): Promise<Project[]> {
  const { userId } = await auth();
  if (!userId) return [];
  const admin = getSupabaseAdmin();
  const { data, error } = await admin
    .from("projects")
    .select("*")
    .eq("owner_id", userId)
    .order("created_at", { ascending: false })
    .limit(limit);
  if (error) {
    console.error("[projects:list] supabase error", error);
    return [];
  }
  return (data ?? []) as Project[];
}

export async function getMyProject(projectId: string): Promise<Project | null> {
  const { userId } = await auth();
  if (!userId) return null;
  const admin = getSupabaseAdmin();
  const { data, error } = await admin
    .from("projects")
    .select("*")
    .eq("id", projectId)
    .eq("owner_id", userId)
    .maybeSingle();
  if (error) {
    console.error("[projects:get] supabase error", error);
    return null;
  }
  return (data as Project) ?? null;
}

export async function listProjectMessages(
  projectId: string,
  limit = 200,
): Promise<ChatMessage[]> {
  const project = await getMyProject(projectId);
  if (!project) return [];
  const admin = getSupabaseAdmin();
  const { data, error } = await admin
    .from("project_messages")
    .select("*")
    .eq("project_id", projectId)
    .order("created_at", { ascending: true })
    .limit(limit);
  if (error) {
    console.error("[projects:messages] supabase error", error);
    return [];
  }
  return (data ?? []) as ChatMessage[];
}

// ---------------------------------------------------------------------------
// Writes
// ---------------------------------------------------------------------------

const CreateProjectSchema = z.object({
  prompt: z.string().trim().min(1).max(8000),
  title: z.string().trim().max(200).optional(),
});

export type CreateProjectFormState = { error: string | null };

/**
 * Server action invoked from /projects/new's chat-style entry form.
 * Creates the project row, seeds the first user message (so the chat
 * thread on the next page already has the prompt visible), and
 * redirects to the project page.
 */
export async function createProjectFromForm(
  _prev: CreateProjectFormState | null,
  formData: FormData,
): Promise<CreateProjectFormState> {
  const { userId } = await auth();
  if (!userId) return { error: "Not signed in." };

  const parsed = CreateProjectSchema.safeParse({
    prompt: String(formData.get("prompt") ?? ""),
  });
  if (!parsed.success) {
    return { error: parsed.error.issues[0]?.message ?? "Invalid input." };
  }

  const admin = getSupabaseAdmin();
  const { data, error } = await admin
    .from("projects")
    .insert({
      owner_id: userId,
      prompt: parsed.data.prompt,
      title: parsed.data.title ?? null,
      status: "draft",
    })
    .select("id")
    .single();

  if (error || !data) {
    console.error("[projects:create] supabase error", error);
    return { error: "Could not create project." };
  }

  // Seed the user's prompt as the first message in the thread so the
  // chat surface on the next page is non-empty.
  const { error: msgErr } = await admin.from("project_messages").insert({
    project_id: data.id,
    role: "user",
    content: parsed.data.prompt,
  });
  if (msgErr) {
    console.error("[projects:create] seed message error", msgErr);
    // Non-fatal — the project still exists, just without the seeded
    // user turn. The chat surface will show an empty thread.
  }

  revalidatePath("/projects");
  redirect(`/projects/${data.id}`);
}

export async function deleteProject(
  projectId: string,
): Promise<{ ok: boolean; error?: string }> {
  const { userId } = await auth();
  if (!userId) return { ok: false, error: "Not signed in." };
  const admin = getSupabaseAdmin();
  const { error } = await admin
    .from("projects")
    .delete()
    .eq("id", projectId)
    .eq("owner_id", userId);
  if (error) {
    console.error("[projects:delete] supabase error", error);
    return { ok: false, error: "Could not delete project." };
  }
  revalidatePath("/projects");
  return { ok: true };
}

export async function deleteProjectFromForm(formData: FormData): Promise<void> {
  const id = String(formData.get("project_id") ?? "");
  if (!id) return;
  const res = await deleteProject(id);
  if (!res.ok) {
    console.error("[projects:delete-form]", res.error);
    return;
  }
  redirect("/projects");
}
