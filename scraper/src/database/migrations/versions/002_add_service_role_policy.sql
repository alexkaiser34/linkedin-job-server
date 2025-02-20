-- Enable row level security on the jobs table if not already enabled
do $$ 
begin
    if not exists (
        select 1
        from pg_tables
        where tablename = 'jobs'
        and rowsecurity = true
    ) then
        alter table jobs enable row level security;
    end if;
end $$;

-- Create policy to allow service_role full access if it doesn't exist
do $$
begin
    if not exists (
        select 1
        from pg_policies
        where tablename = 'jobs'
        and policyname = 'allow_service_role'
    ) then
        create policy "allow_service_role" on jobs
        for all
        to service_role
        using (true)
        with check (true);
    end if;
end $$;