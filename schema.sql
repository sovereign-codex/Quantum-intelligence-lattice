
-- Core tables
create table if not exists public.run (
  id uuid primary key default gen_random_uuid(),
  day int not null,
  ok boolean,
  started_at timestamptz,
  finished_at timestamptz,
  artifacts jsonb
);

create table if not exists public.metric (
  id uuid primary key default gen_random_uuid(),
  day int not null,
  k text not null,
  v double precision,
  ts timestamptz default now()
);

create table if not exists public.vot (
  day int primary key,
  role text,
  theme text
);

create table if not exists public.edge (
  src int not null,
  dst int not null
);

-- RLS
alter table public.run enable row level security;
alter table public.metric enable row level security;
alter table public.vot enable row level security;
alter table public.edge enable row level security;

-- Read policies for anon (dashboard)
do $$ begin
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='run' and policyname='read run') then
    create policy "read run" on public.run for select using (true);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='metric' and policyname='read metric') then
    create policy "read metric" on public.metric for select using (true);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='vot' and policyname='read vot') then
    create policy "read vot" on public.vot for select using (true);
  end if;
  if not exists (select 1 from pg_policies where schemaname='public' and tablename='edge' and policyname='read edge') then
    create policy "read edge" on public.edge for select using (true);
  end if;
end $$;
