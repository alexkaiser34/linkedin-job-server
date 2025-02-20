-- Create function to delete old jobs
create or replace function delete_old_jobs()
returns void
language plpgsql
security definer
as $func$
begin
    delete from jobs
    where created_at < (now() - interval '1 day');
end;
$func$;

-- Grant execute permission to service_role if not already granted
do $$
begin
    if not exists (
        select 1
        from information_schema.routine_privileges
        where routine_name = 'delete_old_jobs'
        and grantee = 'service_role'
        and privilege_type = 'EXECUTE'
    ) then
        grant execute on function delete_old_jobs() to service_role;
    end if;
end $$;