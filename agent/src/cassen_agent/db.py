"""Supabase admin client + the message-thread CRUD the graph uses."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal

from supabase import Client, create_client

from .settings import get_settings


@lru_cache(maxsize=1)
def get_supabase_admin() -> Client:
    """Service-role Supabase client. Bypasses RLS — only call from
    the FastAPI server, never expose to the client."""
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_role_key)


def list_project_messages(
    project_id: str,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Return the most recent `limit` messages, oldest-first. The
    planner reads this to seed Claude's `messages` context so the
    agent's reply continues the existing thread.
    """
    sb = get_supabase_admin()
    res = (
        sb.table("project_messages")
        .select("id, role, content, created_at")
        .eq("project_id", project_id)
        .order("created_at", desc=False)
        .limit(limit)
        .execute()
    )
    rows = res.data or []
    return [r for r in rows if isinstance(r, dict)]


def append_project_message(
    project_id: str,
    *,
    role: Literal["user", "assistant", "system"],
    content: str = "",
    thinking: str | None = None,
    tool_calls: list[dict[str, Any]] | None = None,
    artifacts: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Insert one chat message; return the row (with assigned uuid +
    timestamp) so the caller can stream it back to the client."""
    sb = get_supabase_admin()
    row: dict[str, Any] = {
        "project_id": project_id,
        "role": role,
        "content": content,
    }
    if thinking is not None:
        row["thinking"] = thinking
    if tool_calls is not None:
        row["tool_calls"] = tool_calls
    if artifacts is not None:
        row["artifacts"] = artifacts
    res = sb.table("project_messages").insert(row).execute()
    data = (res.data or [None])[0]
    return data if isinstance(data, dict) else None


def update_project_status(project_id: str, status: str) -> None:
    """Bump `projects.status`. Values must match `projects_status_chk`
    in app/db/migrations/001_init.sql."""
    sb = get_supabase_admin()
    sb.table("projects").update({"status": status}).eq("id", project_id).execute()


def fetch_project(project_id: str) -> dict[str, Any] | None:
    """Pull the project row. Used by the planner to ground its system
    prompt in the project's stated title + prompt without re-asking."""
    sb = get_supabase_admin()
    res = (
        sb.table("projects")
        .select("id, title, prompt, status, auto_mode")
        .eq("id", project_id)
        .maybe_single()
        .execute()
    )
    return res.data if res and isinstance(res.data, dict) else None
