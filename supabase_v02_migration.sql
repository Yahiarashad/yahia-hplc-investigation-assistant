-- Yahia QC Instrument Lifecycle & Investigation Intelligence™
-- v0.2 migration: Maintenance History + Lifecycle Records + Component Lifecycle
-- Safe to run after the v0.1 multi-user schema.

create table if not exists public.maintenance_records (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    instrument_id uuid not null references public.instruments(id) on delete cascade,
    maintenance_date date not null default current_date,
    maintenance_type text not null,
    provider text,
    work_order text,
    actions_taken text not null,
    parts_replaced text,
    result text not null default 'Completed / Pass',
    next_due date,
    notes text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.lifecycle_records (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    instrument_id uuid not null references public.instruments(id) on delete cascade,
    record_type text not null,
    performed_date date not null default current_date,
    result text not null default 'Pass',
    provider text,
    reference text,
    next_due date,
    notes text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.instrument_components (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    instrument_id uuid not null references public.instruments(id) on delete cascade,
    component_name text not null,
    component_type text,
    part_number text,
    serial_number text,
    installed_date date,
    replacement_due date,
    status text not null default 'Active',
    notes text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

drop trigger if exists trg_maintenance_updated_at on public.maintenance_records;
create trigger trg_maintenance_updated_at before update on public.maintenance_records for each row execute function public.set_updated_at();

drop trigger if exists trg_lifecycle_records_updated_at on public.lifecycle_records;
create trigger trg_lifecycle_records_updated_at before update on public.lifecycle_records for each row execute function public.set_updated_at();

drop trigger if exists trg_components_updated_at on public.instrument_components;
create trigger trg_components_updated_at before update on public.instrument_components for each row execute function public.set_updated_at();

alter table public.maintenance_records enable row level security;
alter table public.lifecycle_records enable row level security;
alter table public.instrument_components enable row level security;

-- Maintenance RLS
drop policy if exists "Users can view own maintenance" on public.maintenance_records;
create policy "Users can view own maintenance" on public.maintenance_records for select to authenticated using (auth.uid() = user_id);

drop policy if exists "Users can create own maintenance" on public.maintenance_records;
create policy "Users can create own maintenance" on public.maintenance_records for insert to authenticated with check (
    auth.uid() = user_id and exists (select 1 from public.instruments i where i.id = instrument_id and i.user_id = auth.uid())
);

drop policy if exists "Users can update own maintenance" on public.maintenance_records;
create policy "Users can update own maintenance" on public.maintenance_records for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "Users can delete own maintenance" on public.maintenance_records;
create policy "Users can delete own maintenance" on public.maintenance_records for delete to authenticated using (auth.uid() = user_id);

-- Lifecycle RLS
drop policy if exists "Users can view own lifecycle records" on public.lifecycle_records;
create policy "Users can view own lifecycle records" on public.lifecycle_records for select to authenticated using (auth.uid() = user_id);

drop policy if exists "Users can create own lifecycle records" on public.lifecycle_records;
create policy "Users can create own lifecycle records" on public.lifecycle_records for insert to authenticated with check (
    auth.uid() = user_id and exists (select 1 from public.instruments i where i.id = instrument_id and i.user_id = auth.uid())
);

drop policy if exists "Users can update own lifecycle records" on public.lifecycle_records;
create policy "Users can update own lifecycle records" on public.lifecycle_records for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "Users can delete own lifecycle records" on public.lifecycle_records;
create policy "Users can delete own lifecycle records" on public.lifecycle_records for delete to authenticated using (auth.uid() = user_id);

-- Component RLS
drop policy if exists "Users can view own components" on public.instrument_components;
create policy "Users can view own components" on public.instrument_components for select to authenticated using (auth.uid() = user_id);

drop policy if exists "Users can create own components" on public.instrument_components;
create policy "Users can create own components" on public.instrument_components for insert to authenticated with check (
    auth.uid() = user_id and exists (select 1 from public.instruments i where i.id = instrument_id and i.user_id = auth.uid())
);

drop policy if exists "Users can update own components" on public.instrument_components;
create policy "Users can update own components" on public.instrument_components for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "Users can delete own components" on public.instrument_components;
create policy "Users can delete own components" on public.instrument_components for delete to authenticated using (auth.uid() = user_id);

grant select, insert, update, delete on public.maintenance_records to authenticated;
grant select, insert, update, delete on public.lifecycle_records to authenticated;
grant select, insert, update, delete on public.instrument_components to authenticated;

create index if not exists idx_maintenance_user on public.maintenance_records(user_id);
create index if not exists idx_maintenance_instrument on public.maintenance_records(instrument_id);
create index if not exists idx_maintenance_date on public.maintenance_records(maintenance_date desc);
create index if not exists idx_lifecycle_user on public.lifecycle_records(user_id);
create index if not exists idx_lifecycle_instrument on public.lifecycle_records(instrument_id);
create index if not exists idx_lifecycle_date on public.lifecycle_records(performed_date desc);
create index if not exists idx_components_user on public.instrument_components(user_id);
create index if not exists idx_components_instrument on public.instrument_components(instrument_id);
create index if not exists idx_components_due on public.instrument_components(replacement_due);
