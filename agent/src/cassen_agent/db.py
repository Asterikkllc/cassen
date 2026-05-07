from supabase import Client, create_client

from .settings import get_settings


def get_supabase_admin() -> Client:
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_role_key)


def update_project_status(project_id: str, status: str) -> None:
    sb = get_supabase_admin()
    sb.table("projects").update({"status": status}).eq("id", project_id).execute()


def fetch_project(project_id: str, owner_id: str) -> dict | None:
    sb = get_supabase_admin()
    res = (
        sb.table("projects")
        .select("*")
        .eq("id", project_id)
        .eq("owner_id", owner_id)
        .maybe_single()
        .execute()
    )
    return res.data if res else None


def append_version_snapshot(
    project_id: str,
    snapshot: dict,
    created_by: str,
    note: str | None = None,
) -> None:
    sb = get_supabase_admin()
    sb.table("project_versions").insert(
        {
            "project_id": project_id,
            "snapshot": snapshot,
            "created_by": created_by,
            "note": note,
        }
    ).execute()
