-- v0.4 security hardening after Supabase advisor review

-- Pin search_path for the generic updated_at trigger helper.
alter function public.set_updated_at() set search_path = public, pg_temp;

-- Trigger/security-definer helpers should not be callable directly through REST/RPC.
revoke execute on function public.handle_new_user() from public;
revoke execute on function public.rls_auto_enable() from public;
revoke execute on function public.handle_new_user() from anon, authenticated;
revoke execute on function public.rls_auto_enable() from anon, authenticated;
