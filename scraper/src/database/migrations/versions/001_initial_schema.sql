-- Create the jobs table with initial schema
create table if not exists jobs (
    id uuid default uuid_generate_v4() primary key,
    job_url text not null unique,
    title text not null,
    company text not null,
    location text,
    posted_time text,
    applicants text,
    description text,
    error text,
    created_at timestamp with time zone default timezone('utc'::text, now()),
    updated_at timestamp with time zone default timezone('utc'::text, now())
);

-- Create the trigger function if it doesn't exist
create or replace function trigger_set_timestamp()
returns trigger as $$
begin
    NEW.updated_at = timezone('utc'::text, now());
    return NEW;
end;
$$ language plpgsql;

-- Create the trigger if it doesn't exist
do $$ 
begin
    if not exists (
        select 1
        from pg_trigger
        where tgname = 'set_updated_at'
    ) then
        create trigger set_updated_at
        before update on jobs
        for each row
        execute procedure trigger_set_timestamp();
    end if;
end $$; 