import os, json, datetime
from typing import Dict, Any, Optional

try:
    from supabase import create_client, Client  # supabase-py v2
except Exception as e:
    create_client = None
    Client = None

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

_client: Optional["Client"] = None

def client():
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError("Supabase env vars missing")
        if create_client is None:
            raise RuntimeError("supabase-py not installed. Add `supabase>=2` to requirements.")
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client

def init_db():
    # Tables should be created via SQL migration provided in README.
    return True

def start_run(day: int) -> str:
    sb = client()
    now = datetime.datetime.utcnow().isoformat()
    data = {
        "day": day,
        "ok": None,
        "started_at": now,
        "finished_at": None,
        "artifacts": {}
    }
    res = sb.table("run").insert(data).execute()
    rid = res.data[0]["id"]
    return rid

def finish_run(run_id: str, ok: bool, artifacts: Dict[str, Any] = {}):
    sb = client()
    now = datetime.datetime.utcnow().isoformat()
    sb.table("run").update({"ok": ok, "finished_at": now, "artifacts": artifacts}).eq("id", run_id).execute()

def add_metric(day: int, k: str, v: float):
    sb = client()
    now = datetime.datetime.utcnow().isoformat()
    sb.table("metric").insert({"day": day, "k": k, "v": v, "ts": now}).execute()
