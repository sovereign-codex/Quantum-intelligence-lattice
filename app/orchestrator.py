# app/orchestrator.py
from __future__ import annotations
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
import os, json
from datetime import datetime
from pathlib import Path

# Optional Supabase (safe if libs missing)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"⚠️ Supabase init failed: {e}")

QIL_SECRET = os.getenv("QIL_SECRET", "")
INBOX_DIR = Path("data/inbox")
INBOX_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Quantum Intelligence Lattice")

class HookPayload(BaseModel):
    source: str
    status: str
    file: Optional[str] = None
    timestamp: Optional[str] = None
    extra: Optional[dict] = None

def _ts() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

@app.get("/")
def root():
    return {
        "ok": True,
        "service": "QIL",
        "message": "Listening for breaths and intents.",
        "inbox_count": len(list(INBOX_DIR.glob("*.json"))),
    }

@app.post("/hook")
async def hook(req: Request):
    # Shared-secret check
    secret = req.headers.get("X-QIL-Secret", "")
    if not QIL_SECRET or secret != QIL_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await req.json()
    payload = HookPayload(**data)

    # Persist locally
    path = INBOX_DIR / f"{payload.source}-{_ts()}.json"
    path.write_text(json.dumps(payload.dict(), indent=2), encoding="utf-8")

    # Optional: mirror to Supabase
    if supabase:
        try:
            supabase.table("qil_inbox").insert({
                "source": payload.source,
                "status": payload.status,
                "file": payload.file,
                "timestamp": payload.timestamp or datetime.utcnow().isoformat() + "Z",
                "extra": payload.extra or {},
            }).execute()
        except Exception as e:
            print(f"⚠️ Supabase insert failed: {e}")

    return {"ok": True, "stored": str(path)}