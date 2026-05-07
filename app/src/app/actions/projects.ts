"use server";

import { z } from "zod";
import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { auth } from "@clerk/nextjs/server";
import { getSupabaseAdmin } from "@/lib/supabase";
import type { Project } from "@/lib/projects-types";

const CreateInputSchema = z.object({
  prompt: z.string().trim().min(1).max(8000),
  title: z.string().trim().max(200).optional(),
});

export type CreateProjectInput = z.infer<typeof CreateInputSchema>;

export type CreateProjectResult =
  | { ok: true; project: Project }
  | { ok: false; error: string };

export async function createProject(
  input: CreateProjectInput,
): Promise<CreateProjectResult> {
  const { userId } = await auth();
  if (!userId) return { ok: false, error: "Not signed in." };

  const parsed = CreateInputSchema.safeParse(input);
  if (!parsed.success) {
    return {
      ok: false,
      error: parsed.error.issues[0]?.message ?? "Invalid input.",
    };
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
    .select("*")
    .single();

  if (error) {
    console.error("[projects:create] supabase error", error);
    return { ok: false, error: "Could not create project." };
  }

  return { ok: true, project: data as Project };
}

export type CreateProjectFormState = {
  error: string | null;
};

export async function createProjectFromForm(
  _prev: CreateProjectFormState | null,
  formData: FormData,
): Promise<CreateProjectFormState> {
  const prompt = String(formData.get("prompt") ?? "");
  const result = await createProject({ prompt });
  if (!result.ok) {
    return { error: result.error };
  }
  revalidatePath("/projects");
  redirect(`/projects/${result.project.id}`);
}

export async function listMyProjects(limit = 50): Promise<Project[]> {
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

export type DeleteProjectResult =
  | { ok: true }
  | { ok: false; error: string };

export async function deleteProject(
  projectId: string,
): Promise<DeleteProjectResult> {
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
