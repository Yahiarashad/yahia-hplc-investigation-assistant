-- Yahia QC Instrument Lifecycle & Investigation Intelligence™
-- v0.3 migration: Calibration Control Center

create table if not exists public.calibration_records (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    instrument_id uuid not null references public.instruments(id) on delete cascade,
    calibration_date date not null default current_date,
    calibration_type text not null default 'Routine',
    result text not null default 'Pass',
    calibration_id text,
    certificate_number text,
    report_reference text,
    raw_data_reference text,
    maintenance_reference text,
    next_due date,
    provider text,
    provider_type text not null default 'Internal',
    accreditation_body text,
    accreditation_number text,
    accreditation_scope_confirmed boolean not null default false,
    sop_reference text,
    manufacturer_recommendation_checked boolean not null default false,
    applicable_standard text,
    acceptance_criteria text,
    reference_standards text,
    traceability_reference text,
    as_found text,
    as_left text,
    what_happened text,
    cause_status text not null default 'Not assessed',
    why_happened text,
    impact_assessment text,
    affected_results_products text,
    investigation_reference text,
    deviation_reference text,
    capa_reference text,
    ooc_status text not null default 'Not applicable',
    notes text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

drop trigger if exists trg_calibration_records_updated_at on public.calibration_records;
create trigger trg_calibration_records_updated_at
before update on public.calibration_records
for each row execute function public.set_updated_at();

alter table public.calibration_records enable row level security;

drop policy if exists "Users can view own calibration records" on public.calibration_records;
create policy "Users can view own calibration records"
on public.calibration_records for select to authenticated
using (auth.uid() = user_id);

drop policy if exists "Users can create own calibration records" on public.calibration_records;
create policy "Users can create own calibration records"
on public.calibration_records for insert to authenticated
with check (
    auth.uid() = user_id
    and exists (
        select 1 from public.instruments i
        where i.id = instrument_id and i.user_id = auth.uid()
    )
);

drop policy if exists "Users can update own calibration records" on public.calibration_records;
create policy "Users can update own calibration records"
on public.calibration_records for update to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

drop policy if exists "Users can delete own calibration records" on public.calibration_records;
create policy "Users can delete own calibration records"
on public.calibration_records for delete to authenticated
using (auth.uid() = user_id);

grant select, insert, update, delete on public.calibration_records to authenticated;

create index if not exists idx_calibration_records_user on public.calibration_records(user_id);
create index if not exists idx_calibration_records_instrument on public.calibration_records(instrument_id);
create index if not exists idx_calibration_records_date on public.calibration_records(calibration_date desc);
create index if not exists idx_calibration_records_due on public.calibration_records(next_due);
create index if not exists idx_calibration_records_ooc on public.calibration_records(ooc_status);
