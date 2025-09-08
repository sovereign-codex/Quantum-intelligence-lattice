# QIL – 365 VOT Orchestrator (Starter)

This is a **multi-tenant agent lattice** starter that loads your 365-day plan from CSV,
builds a dependency DAG, and executes VOT jobs in parallel using an async worker pool.
Each VOT is a *role behavior plugin* (reusable across many days).

## Quick start (local or Replit)

```bash
# 1) Python 3.10+ recommended
pip install -r requirements.txt

# 2) Run the API (spawns orchestrator on /start)
uvicorn app.main:app --reload --port 8080
```

Open: `http://localhost:8080/docs`

### Endpoints
- `POST /start` → begins processing VOT DAG with a worker pool
- `GET  /status` → returns counts for Open/In-Progress/Done
- `POST /stop` → requests graceful stop

Artifacts are written to `./artifacts/`.
A simple SQLite ledger is created at `./qil.db`.

> Swap to Supabase/Postgres later by replacing `app/infra/db.py`.

## CLI (no API)
Run a one-shot orchestrator loop without FastAPI:
```bash
python app/main.py --cli
```

## Behavior plugins
Add new role behaviors under `app/behaviors/`. Each file implements:

```python
async def run(vot: dict, ctx: dict) -> dict:
    # return a dict of metrics (e.g., {"tokens": 1234, "files_created": 1})
```

## CSV schema
This project expects the CSV you already have:
`QIL_365_VOT_Metrics_Plan.csv` with headers:

- Day, Date, Theme, VOT Name, Primary Deliverable,
  Key Metrics (template), Status, Dependencies (Day #)

Place it in `./data/` or set `QIL_CSV` env var.

################################################################################
## Supabase wiring (server-side)

1) Create a new Supabase project.  
2) Run this SQL in the Supabase SQL editor to create tables and policies:

```sql
-- Tables
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

-- Row Level Security
alter table public.run enable row level security;
alter table public.metric enable row level security;

-- Service role can bypass RLS. For anon key (if you expose a read-only dashboard), add read policies:
create policy "read run" on public.run for select using (true);
create policy "read metric" on public.metric for select using (true);

-- Optional write policies if you must write with anon (not recommended). Prefer service_role on server.
```

3) Set env vars in your runtime (Replit/Fly/Render):
- `SUPABASE_URL`, `SUPABASE_KEY` (service_role server key)
- `QIL_DB_BACKEND=supabase`

4) Install deps: `pip install -r requirements.txt`

5) Start the API and POST `/start` as before.

################################################################################
## Supabase Storage (artifacts)

Create a bucket named from env `QIL_BUCKET` (default `artifacts`). For public links, make the bucket public
or set a CDN/public base via `QIL_PUBLIC_URL` (e.g., your Storage CDN URL). The code will fall back to signed URLs.

### Optional: enable public read on bucket
In Supabase Storage, mark the bucket as public. Or keep it private and rely on signed URLs.

### Env
- `QIL_BUCKET=artifacts`
- `QIL_PUBLIC_URL=https://your-project.supabase.co/storage/v1/object/public/artifacts` (if bucket is public)

Artifacts are uploaded automatically by behaviors; the orchestrator saves the returned URL inside `run.artifacts`.
