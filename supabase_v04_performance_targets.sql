-- v0.4 Instrument performance targets
-- User-defined management thresholds for monthly Availability and Utilization.
-- These targets are decision-support indicators, not GMP release criteria.

alter table public.instruments
  add column if not exists target_availability_pct numeric(5,2),
  add column if not exists target_utilization_pct numeric(5,2),
  add column if not exists performance_target_note text;

alter table public.instruments
  drop constraint if exists instruments_target_availability_pct_check,
  add constraint instruments_target_availability_pct_check
    check (
      target_availability_pct is null
      or (target_availability_pct >= 0 and target_availability_pct <= 100)
    ),
  drop constraint if exists instruments_target_utilization_pct_check,
  add constraint instruments_target_utilization_pct_check
    check (
      target_utilization_pct is null
      or (target_utilization_pct >= 0 and target_utilization_pct <= 100)
    );
