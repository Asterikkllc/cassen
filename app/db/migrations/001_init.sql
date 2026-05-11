-- Cassen — initial schema for the rebuilt product surface.
--
-- Two tables for slice 0:
--   public.projects          — one row per user project. Clerk user id
--                              owns the row via `owner_id` (text since
--                              Clerk emits its own ids, not uuids).
--   public.project_messages  — chat thread per project (user, assistant,
--                              system). Each message can carry
--                              `thinking` + `tool_calls` + `artifacts`
--                              for future agent integrations without a
--                              schema migration.
--
-- Both are service-role-only — no anon/authenticated access. The app
-- talks to Supabase exclusively via the service-role key behind Clerk
-- auth, so RLS is a defense-in-depth measure, not the primary gate.

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------
-- helpers
-- ---------------------------------------------------------------------

create or replace function public.set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- ---------------------------------------------------------------------
-- projects
-- ---------------------------------------------------------------------

create table if not exists public.projects (
  id          uuid primary key default gen_random_uuid(),
  owner_id    text not null,
  title       text,
  prompt      text not null,
  status      text not null default 'draft',
  metadata    jsonb,
  auto_mode   boolean not null default false,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),

  constraint projects_owner_id_format_chk
    check (char_length(owner_id) between 1 and 64),
  constraint projects_title_length_chk
    check (title is null or char_length(title) <= 200),
  constraint projects_prompt_length_chk
    check (char_length(prompt) between 1 and 8000),
  constraint projects_status_chk
    check (status in (
      'draft', 'planning', 'designing', 'simulating',
      'sourcing', 'fabricating', 'assembled', 'shipped',
      'archived', 'failed'
    )),
  constraint projects_metadata_size_chk
    check (metadata is null or octet_length(metadata::text) <= 65536)
);

create index if not exists projects_owner_id_created_at_idx
  on public.projects (owner_id, created_at desc);
create index if not exists projects_owner_id_status_idx
  on public.projects (owner_id, status);

drop trigger if exists projects_set_updated_at on public.projects;
create trigger projects_set_updated_at
  before update on public.projects
  for each row
  execute function public.set_updated_at();

-- ---------------------------------------------------------------------
-- project_messages
-- ---------------------------------------------------------------------

create table if not exists public.project_messages (
  id          uuid primary key default gen_random_uuid(),
  project_id  uuid not null references public.projects(id) on delete cascade,
  role        text not null,
  content     text not null default '',
  thinking    text,
  tool_calls  jsonb,
  artifacts   jsonb,
  created_at  timestamptz not null default now(),

  constraint project_messages_role_chk
    check (role in ('user', 'assistant', 'system')),
  constraint project_messages_content_size_chk
    check (octet_length(content) <= 65536),
  constraint project_messages_thinking_size_chk
    check (thinking is null or octet_length(thinking) <= 262144),
  constraint project_messages_tool_calls_size_chk
    check (tool_calls is null or octet_length(tool_calls::text) <= 524288),
  constraint project_messages_artifacts_size_chk
    check (artifacts is null or octet_length(artifacts::text) <= 65536)
);

create index if not exists project_messages_project_created_idx
  on public.project_messages (project_id, created_at);

-- ---------------------------------------------------------------------
-- RLS — service-role-only
-- ---------------------------------------------------------------------

alter table public.projects enable row level security;
alter table public.projects force  row level security;
alter table public.project_messages enable row level security;
alter table public.project_messages force  row level security;

revoke all on table public.projects         from public;
revoke all on table public.projects         from anon;
revoke all on table public.projects         from authenticated;
revoke all on table public.project_messages from public;
revoke all on table public.project_messages from anon;
revoke all on table public.project_messages from authenticated;

grant  all on table public.projects         to service_role;
grant  all on table public.project_messages to service_role;
