-- Yahia QC Instrument Intelligence™
-- v0.6 Multi-tenant workspace foundation.
-- IMPORTANT: use this INSTEAD OF running v0.5 RBAC on production.
-- It preserves current personal data by creating one Personal Workspace per existing user.
-- No existing business row is deleted.

create table if not exists public.qc_workspaces (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  workspace_type text not null default 'personal' check (workspace_type in ('personal','organization')),
  created_by uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.qc_workspace_members (
  workspace_id uuid not null references public.qc_workspaces(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  job_role text not null default 'QC Analyst',
  access_role text not null default 'Member',
  account_status text not null default 'active' check (account_status in ('pending','active','suspended')),
  is_admin boolean not null default false,
  permissions jsonb not null default '{}'::jsonb,
  joined_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key(workspace_id,user_id)
);

create table if not exists public.qc_access_audit (
  id bigint generated always as identity primary key,
  workspace_id uuid not null references public.qc_workspaces(id) on delete cascade,
  actor_user_id uuid references auth.users(id) on delete set null,
  target_user_id uuid references auth.users(id) on delete set null,
  action text not null,
  module text,
  record_table text,
  record_id text,
  old_value jsonb,
  new_value jsonb,
  reason text,
  created_at timestamptz not null default now()
);

create or replace function public.is_workspace_member(p_workspace uuid)
returns boolean language sql stable security definer set search_path=public as $$
 select exists(select 1 from public.qc_workspace_members m
   where m.workspace_id=p_workspace and m.user_id=auth.uid() and m.account_status='active');
$$;

create or replace function public.is_workspace_admin(p_workspace uuid)
returns boolean language sql stable security definer set search_path=public as $$
 select exists(select 1 from public.qc_workspace_members m
   where m.workspace_id=p_workspace and m.user_id=auth.uid()
     and m.account_status='active' and m.is_admin);
$$;

create or replace function public.workspace_has_permission(p_workspace uuid,p_module text,p_action text)
returns boolean language sql stable security definer set search_path=public as $$
 select coalesce(
   (select m.account_status='active' and
      (m.is_admin or coalesce((m.permissions->p_module->>p_action)::boolean,false))
    from public.qc_workspace_members m
    where m.workspace_id=p_workspace and m.user_id=auth.uid()),false);
$$;

-- Bootstrap one personal workspace for every existing application user.
insert into public.qc_workspaces(name,workspace_type,created_by)
select coalesce(nullif(u.raw_user_meta_data->>'display_name',''),split_part(u.email,'@',1)) || ' · Personal Workspace',
       'personal',u.id
from auth.users u
where not exists(select 1 from public.qc_workspaces w where w.created_by=u.id and w.workspace_type='personal');

insert into public.qc_workspace_members(workspace_id,user_id,job_role,access_role,account_status,is_admin,permissions)
select w.id,w.created_by,'QC Analyst','Owner','active',true,'{}'::jsonb
from public.qc_workspaces w
where w.workspace_type='personal'
on conflict(workspace_id,user_id) do nothing;

-- Add tenant key without destroying the legacy owner key.
do $$
declare t text;
begin
  foreach t in array array[
    'instruments','instrument_events','investigations','maintenance_records','lifecycle_records',
    'instrument_components','instrument_performance_reviews','instrument_retirements',
    'calibration_records','instrument_monthly_performance'
  ] loop
    if to_regclass('public.'||t) is not null then
      execute format('alter table public.%I add column if not exists workspace_id uuid references public.qc_workspaces(id)',t);
      execute format(
        'update public.%I x set workspace_id=w.id from public.qc_workspaces w where x.workspace_id is null and w.created_by=x.user_id and w.workspace_type=''personal''',t);
      execute format('create index if not exists %I on public.%I(workspace_id)', 'idx_'||t||'_workspace',t);
    end if;
  end loop;
end $$;

-- New rows can derive workspace explicitly. Existing user_id remains actor/creator provenance.
-- Do NOT remove user_id: it is valuable audit provenance.

alter table public.qc_workspaces enable row level security;
alter table public.qc_workspace_members enable row level security;
alter table public.qc_access_audit enable row level security;

drop policy if exists "Members view workspace" on public.qc_workspaces;
create policy "Members view workspace" on public.qc_workspaces for select to authenticated
using (public.is_workspace_member(id));
drop policy if exists "Creator creates workspace" on public.qc_workspaces;
create policy "Creator creates workspace" on public.qc_workspaces for insert to authenticated
with check (created_by=auth.uid());
drop policy if exists "Admins update workspace" on public.qc_workspaces;
create policy "Admins update workspace" on public.qc_workspaces for update to authenticated
using (public.is_workspace_admin(id)) with check(public.is_workspace_admin(id));

drop policy if exists "Members view members" on public.qc_workspace_members;
create policy "Members view members" on public.qc_workspace_members for select to authenticated
using (public.is_workspace_member(workspace_id));
drop policy if exists "Admins add members" on public.qc_workspace_members;
create policy "Admins add members" on public.qc_workspace_members for insert to authenticated
with check(public.is_workspace_admin(workspace_id));
drop policy if exists "Admins update members" on public.qc_workspace_members;
create policy "Admins update members" on public.qc_workspace_members for update to authenticated
using(public.is_workspace_admin(workspace_id)) with check(public.is_workspace_admin(workspace_id));
drop policy if exists "Admins remove members" on public.qc_workspace_members;
create policy "Admins remove members" on public.qc_workspace_members for delete to authenticated
using(public.is_workspace_admin(workspace_id));

drop policy if exists "Admins read access audit" on public.qc_access_audit;
create policy "Admins read access audit" on public.qc_access_audit for select to authenticated
using(public.is_workspace_admin(workspace_id));
drop policy if exists "Members write own access audit" on public.qc_access_audit;
create policy "Members write own access audit" on public.qc_access_audit for insert to authenticated
with check(actor_user_id=auth.uid() and public.is_workspace_member(workspace_id));

grant select,insert,update on public.qc_workspaces to authenticated;
grant select,insert,update,delete on public.qc_workspace_members to authenticated;
grant select,insert on public.qc_access_audit to authenticated;
grant usage,select on sequence public.qc_access_audit_id_seq to authenticated;
grant execute on function public.is_workspace_member(uuid) to authenticated;
grant execute on function public.is_workspace_admin(uuid) to authenticated;
grant execute on function public.workspace_has_permission(uuid,text,text) to authenticated;

-- SECURITY CUTOVER NOTE
-- The current business-table policies still isolate by user_id after this migration.
-- That is intentional for a safe two-phase rollout. Do NOT drop them yet.
-- Phase 2 will replace each business-table RLS policy with workspace_id +
-- workspace_has_permission(...) after the UI writes/reads the active workspace correctly.
