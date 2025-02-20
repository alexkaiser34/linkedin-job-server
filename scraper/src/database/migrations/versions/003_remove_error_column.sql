-- Remove error column from jobs table if it exists
do $$
begin
    if exists (
        select 1
        from information_schema.columns
        where table_name = 'jobs'
        and column_name = 'error'
    ) then
        alter table jobs
        drop column error;
    end if;
end $$; 