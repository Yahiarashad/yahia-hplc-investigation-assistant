-- Yahia QC Instrument Lifecycle & Investigation Intelligence™
-- v0.3 lifecycle foundation
-- Applied to Supabase production project on 2026-09-19.

alter table public.instruments
    add column if not exists need_title text,
    add column if not exists need_identified_date date,
    add column if not exists requested_by text,
    add column if not exists department text,
    add column if not exists need_justification text,
    add column if not exists intended_use text,
    add column if not exists criticality text default 'Medium',
    add column if not exists target_implementation_date date,
    add column if not exists installation_date date,
    add column if not exists installation_reference text,
    add column if not exists site_readiness_confirmed boolean not null default false,
    add column if not exists utilities_confirmed boolean not null default false;

create table if not exists public.instrument_performance_reviews (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    instrument_id uuid not null references public.instruments(id) on delete cascade,
    review_date date not null default current_date,
    review_period_months integer not null default 12,
    calibration_compliance_pct numeric,
    pm_compliance_pct numeric,
    failure_count integer,
    ooc_count integer,
    repeated_pattern_notes text,
    health_summary text,
    decision text not null default 'Continue as-is',
    action_plan text,
    reviewed_by text,
    notes text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.instrument_retirements (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    instrument_id uuid not null unique references public.instruments(id) on delete cascade,
    retirement_request_date date,
    retirement_reason text,
    replacement_instrument text,
    approval_date date,
    decommission_date date,
    data_archive_completed boolean not null default false,
    backup_completed boolean not null default false,
    software_access_disabled boolean not null default false,
    labels_removed boolean not null default false,
    disposal_method text,
    disposal_reference text,
    approved_by text,
    notes text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

drop trigger if exists trg_performance_reviews_updated_at on public.instrument_performance_reviews;
create trigger trg_performance_reviews_updated_at before update on public.instrument_performance_reviews for each row execute function public.set_updated_at();

drop trigger if exists trg_retirements_updated_at on public.instrument_retirements;
create trigger trg_retirements_updated_at before update on public.instrument_retirements for each row execute function public.set_updated_at();

alter table public.instrument_performance_reviews enable row level security;
alter table public.instrument_retirements enable row level security;

drop policy if exists "Users can view own performance reviews" on public.instrument_performance_reviews;
create policy "Users can view own performance reviews" on public.instrument_performance_reviews for select to authenticated using (auth.uid() = user_id);
drop policy if exists "Users can create own performance reviews" on public.instrument_performance_reviews;
create policy "Users can create own performance reviews" on public.instrument_performance_reviews for insert to authenticated with check (auth.uid() = user_id and exists (select 1 from public.instruments i where i.id = instrument_id and i.user_id = auth.uid()));
drop policy if exists "Users can update own performance reviews" on public.instrument_performance_reviews;
create policy "Users can update own performance reviews" on public.instrument_performance_reviews for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id and exists (select 1 from public.instruments i where i.id = instrument_id and i.user_id = auth.uid()));
drop policy if exists "Users can delete own performance reviews" on public.instrument_performance_reviews;
create policy "Users can delete own performance reviews" on public.instrument_performance_reviews for delete to authenticated using (auth.uid() = user_id);

drop policy if exists "Users can view own retirements" on public.instrument_retirements;
create policy "Users can view own retirements" on public.instrument_retirements for select to authenticated using (auth.uid() = user_id);
drop policy if exists "Users can create own retirements" on public.instrument_retirements;
create policy "Users can create own retirements" on public.instrument_retirements for insert to authenticated with check (auth.uid() = user_id and exists (select 1 from public.instruments i where i.id = instrument_id and i.user_id = auth.uid()));
drop policy if exists "Users can update own retirements" on public.instrument_retirements;
create policy "Users can update own retirements" on public.instrument_retirements for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id and exists (select 1 from public.instruments i where i.id = instrument_id and i.user_id = auth.uid()));
drop policy if exists "Users can delete own retirements" on public.instrument_retirements;
create policy "Users can delete own retirements" on public.instrument_retirements for delete to authenticated using (auth.uid() = user_id);

grant select, insert, update, delete on public.instrument_performance_reviews to authenticated;
grant select, insert, update, delete on public.instrument_retirements to authenticated;

create index if not exists idx_performance_reviews_user on public.instrument_performance_reviews(user_id);
create index if not exists idx_performance_reviews_instrument on public.instrument_performance_reviews(instrument_id);
create index if not exists idx_performance_reviews_date on public.instrument_performance_reviews(review_date desc);
create index if not exists idx_retirements_user on public.instrument_retirements(user_id);
create index if not exists idx_retirements_instrument on public.instrument_retirements(instrument_id);
