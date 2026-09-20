-- v0.3 Monthly Instrument Performance
-- Availability + Utilization, one row per instrument per month.

create table if not exists public.instrument_monthly_performance (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
    instrument_id uuid not null references public.instruments(id) on delete cascade,
    month_start date not null,
    scheduled_hours numeric(10,2) not null default 0 check (scheduled_hours >= 0),
    planned_downtime_hours numeric(10,2) not null default 0 check (planned_downtime_hours >= 0),
    unplanned_downtime_hours numeric(10,2) not null default 0 check (unplanned_downtime_hours >= 0),
    productive_run_hours numeric(10,2) not null default 0 check (productive_run_hours >= 0),
    notes text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint instrument_monthly_performance_month_start_check
      check (month_start = date_trunc('month', month_start)::date),
    constraint instrument_monthly_performance_planned_check
      check (planned_downtime_hours <= scheduled_hours),
    constraint instrument_monthly_performance_unplanned_check
      check (unplanned_downtime_hours <= scheduled_hours - planned_downtime_hours),
    constraint instrument_monthly_performance_productive_check
      check (productive_run_hours <= scheduled_hours - planned_downtime_hours - unplanned_downtime_hours),
    constraint instrument_monthly_performance_unique
      unique (user_id, instrument_id, month_start)
);

drop trigger if exists trg_instrument_monthly_performance_updated_at
on public.instrument_monthly_performance;
create trigger trg_instrument_monthly_performance_updated_at
before update on public.instrument_monthly_performance
for each row execute function public.set_updated_at();

alter table public.instrument_monthly_performance enable row level security;

drop policy if exists "Users can view own monthly performance"
on public.instrument_monthly_performance;
create policy "Users can view own monthly performance"
on public.instrument_monthly_performance for select to authenticated
using (auth.uid() = user_id);

drop policy if exists "Users can create own monthly performance"
on public.instrument_monthly_performance;
create policy "Users can create own monthly performance"
on public.instrument_monthly_performance for insert to authenticated
with check (
  auth.uid() = user_id
  and exists (
    select 1 from public.instruments i
    where i.id = instrument_id and i.user_id = auth.uid()
  )
);

drop policy if exists "Users can update own monthly performance"
on public.instrument_monthly_performance;
create policy "Users can update own monthly performance"
on public.instrument_monthly_performance for update to authenticated
using (auth.uid() = user_id)
with check (
  auth.uid() = user_id
  and exists (
    select 1 from public.instruments i
    where i.id = instrument_id and i.user_id = auth.uid()
  )
);

drop policy if exists "Users can delete own monthly performance"
on public.instrument_monthly_performance;
create policy "Users can delete own monthly performance"
on public.instrument_monthly_performance for delete to authenticated
using (auth.uid() = user_id);

grant select, insert, update, delete
on public.instrument_monthly_performance to authenticated;

create index if not exists idx_instrument_monthly_performance_user_month
on public.instrument_monthly_performance(user_id, month_start desc);
create index if not exists idx_instrument_monthly_performance_instrument_month
on public.instrument_monthly_performance(instrument_id, month_start desc);
