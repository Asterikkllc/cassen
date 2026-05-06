create extension if not exists pgcrypto;

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

create table if not exists public.projects (
  id          uuid primary key default gen_random_uuid(),
  owner_id    text not null,
  title       text,
  prompt      text not null,
  status      text not null default 'draft',
  metadata    jsonb,
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

create table if not exists public.project_versions (
  id          uuid primary key default gen_random_uuid(),
  project_id  uuid not null references public.projects(id) on delete cascade,
  snapshot    jsonb not null,
  created_by  text not null,
  note        text,
  created_at  timestamptz not null default now(),

  constraint project_versions_created_by_format_chk
    check (char_length(created_by) between 1 and 64),
  constraint project_versions_note_length_chk
    check (note is null or char_length(note) <= 500),
  constraint project_versions_snapshot_size_chk
    check (octet_length(snapshot::text) <= 4194304)
);

create index if not exists project_versions_project_created_idx
  on public.project_versions (project_id, created_at desc);

alter table public.projects enable row level security;
alter table public.projects force  row level security;
alter table public.project_versions enable row level security;
alter table public.project_versions force  row level security;

revoke all on table public.projects from public;
revoke all on table public.projects from anon;
revoke all on table public.projects from authenticated;
revoke all on table public.project_versions from public;
revoke all on table public.project_versions from anon;
revoke all on table public.project_versions from authenticated;

grant all on table public.projects         to service_role;
grant all on table public.project_versions to service_role;
