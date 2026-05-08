-- Phase 6b+ requires `researching` as a project status. The original
-- schema.sql only listed draft/planning/designing/.../failed.
-- Idempotent: drops and re-creates the CHECK with the extended set.
--
-- Apply once via Supabase SQL editor (or `supabase db push`); safe
-- to re-run.

alter table public.projects
  drop constraint if exists projects_status_chk;

alter table public.projects
  add constraint projects_status_chk
  check (status in (
    'draft', 'planning', 'researching', 'designing', 'simulating',
    'sourcing', 'fabricating', 'assembled', 'shipped',
    'archived', 'failed'
  ));
