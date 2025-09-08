import os

backend = os.environ.get("QIL_DB_BACKEND", "sqlite").lower()

if backend == "supabase":
    from .db_supabase import init_db, start_run, finish_run, add_metric  # type: ignore
else:
    from .db import init_db, start_run, finish_run, add_metric  # type: ignore
