-- Yahia QC Instrument Intelligence™
-- v0.5 RBAC foundation: admin-controlled privileges + audit trail.
-- Run in Supabase SQL Editor AFTER the existing lifecycle migrations.
-- SECURITY: the database remains authoritative. UI hiding is never treated as access control.

create table if not exists public.app_user_access (
    user_id uuid primary key references auth.users(id) on delete cascade,
    display_name text,
    app_role text not null default 'QC Analyst',
    account_status text not null default 'pending' check (account_status in ('pending','active','suspended')),
    is_admin boolean not null default false,
    permissions jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.app_audit_log (
    id bigint generated always as identity primary key,
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

alter table public.app_user_access enable row level security;
alter table public.app_audit_log enable row level security;

create or replace function public.is_app_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select coalesce((select a.is_admin and a.account_status='active'
                   from public.app_user_access a where a.user_id=auth.uid()), false);
$$;

create or replace function public.has_app_permission(p_module text, p_action text)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select coalesce(
    public.is_app_admin() or
    (select (a.account_status='active') and
            coalesce((a.permissions -> p_module ->> p_action)::boolean, false)
       from public.app_user_access a where a.user_id=auth.uid()),
    false
  );
$$;

drop policy if exists "User reads own access" on public.app_user_access;
create policy "User reads own access" on public.app_user_access
for select to authenticated using (user_id=auth.uid() or public.is_app_admin());

drop policy if exists "Admin inserts access" on public.app_user_access;
create policy "Admin inserts access" on public.app_user_access
for insert to authenticated with check (public.is_app_admin());

drop policy if exists "Admin updates access" on public.app_user_access;
create policy "Admin updates access" on public.app_user_access
for update to authenticated using (public.is_app_admin()) with check (public.is_app_admin());

drop policy if exists "Admin deletes access" on public.app_user_access;
create policy "Admin deletes access" on public.app_user_access
for delete to authenticated using (public.is_app_admin());

drop policy if exists "Admin reads audit" on public.app_audit_log;
create policy "Admin reads audit" on public.app_audit_log
for select to authenticated using (public.is_app_admin());

drop policy if exists "Authenticated inserts own audit" on public.app_audit_log;
create policy "Authenticated inserts own audit" on public.app_audit_log
for insert to authenticated with check (actor_user_id=auth.uid());

grant select, insert, update, delete on public.app_user_access to authenticated;
grant select, insert on public.app_audit_log to authenticated;
grant usage, select on sequence public.app_audit_log_id_seq to authenticated;
grant execute on function public.is_app_admin() to authenticated;
grant execute on function public.has_app_permission(text,text) to authenticated;

-- IMPORTANT BOOTSTRAP:
-- After creating this schema, make ONE existing account the first admin manually:
-- insert into public.app_user_access(user_id,display_name,app_role,account_status,is_admin,permissions)
-- values ('YOUR_AUTH_USER_UUID','System Admin','Admin','active',true,'{}'::jsonb)
-- on conflict(user_id) do update set is_admin=true, account_status='active', app_role='Admin';
--
-- Do NOT expose service-role keys in Streamlit/GitHub.
