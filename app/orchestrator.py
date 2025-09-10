# app/orchestrator.py
# QIL: receive breath signals, verify, weight, stream, and serve history.

import os, json, asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Request, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Optional Supabase (off by default)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"⚠️ Supabase init failed: {e}")

# Optional Ed25519 verification
try:
    import nacl.signing, nacl.encoding, nacl.exceptions  # type: ignore
    HAVE_NACL = True
except Exception:
    HAVE_NACL = False

QIL_SECRET = os.getenv("QIL_SECRET")  # set this in Replit Secrets
DATA_DIR = Path("data"); DATA_DIR.mkdir(exist_ok=True)
INBOX_DIR = DATA_DIR / "inbox"; INBOX_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = DATA_DIR / "events.jsonl"  # line-delimited JSON

# Trust registry: tune weight & verification policy per source
TRUST: Dict[str, Dict[str, Any]] = {
    # source: {weight: 0..1, require_verified: bool, pubkey: hex or None}
    "dream-console": {"weight": 1.0, "require_verified": False, "pubkey": None},
    "manual-test":   {"weight": 0.3, "require_verified": False, "pubkey": None},
}

def source_profile(src: str) -> Dict[str, Any]:
    return TRUST.get(src, {"weight": 0.2, "require_verified": False, "pubkey": None})

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def verify_ed25519(pk_hex: str, content: str, sig_hex: str) -> bool:
    if not HAVE_NACL:
        return False
    try:
        key = nacl.signing.VerifyKey(pk_hex, encoder=nacl.encoding.HexEncoder)
        key.verify(content.encode("utf-8"), nacl.encoding.HexEncoder.decode(sig_hex))
        return True
    except Exception:
        return False

# SSE subscribers
SUBSCRIBERS: List[asyncio.Queue] = []

async def sse_event_generator(q: asyncio.Queue):
    try:
        while True:
            item = await q.get()
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
    except asyncio.CancelledError:
        return

class BreathSignal(BaseModel):
    source: str
    status: str
    file: Optional[str] = None
    timestamp: Optional[str] = None
    extra: Optional[dict] = None  # may include signature/public_key/content or any metadata

app = FastAPI(title="QIL Orchestrator", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

def _auth_ok(token: Optional[str]) -> bool:
    expected = f"Bearer {QIL_SECRET}" if QIL_SECRET else None
    return bool(expected) and (token == expected)

def _append_log(record: dict):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

@app.get("/health")
def health():
    return {"ok": True, "time": now_iso(), "have_supabase": bool(supabase), "have_nacl": HAVE_NACL}

@app.get("/last")
def last():
    if not LOG_FILE.exists():
        return {"ok": True, "event": None}
    try:
        *_, line = LOG_FILE.read_text(encoding="utf-8").splitlines()
        return {"ok": True, "event": json.loads(line)}
    except Exception:
        return {"ok": True, "event": None}

@app.get("/since")
def since(ts: str = Query(..., description="ISO timestamp (UTC)")):
    rows: List[dict] = []
    if LOG_FILE.exists():
        with LOG_FILE.open() as f:
            for line in f:
                try:
                    r = json.loads(line)
                    if r.get("received_at", "") >= ts:
                        rows.append(r)
                except Exception:
                    pass
    return {"ok": True, "items": rows}

@app.get("/stream")
async def stream():
    q = asyncio.Queue()
    SUBSCRIBERS.append(q)
    return StreamingResponse(sse_event_generator(q), media_type="text/event-stream")

@app.post("/hook")
async def hook(signal: BreathSignal, authorization: Optional[str] = Header(None)):
    if not _auth_ok(authorization):
        raise HTTPException(status_code=403, detail="Forbidden")

    rec: Dict[str, Any] = signal.dict()
    rec["received_at"] = now_iso()

    prof = source_profile(signal.source)
    rec["weight"] = prof["weight"]

    # Optional signature verification (if supplied and a key is known)
    verified = False
    if signal.extra and isinstance(signal.extra, dict):
        sig = signal.extra.get("signature")
        content = signal.extra.get("content")
        pk = prof.get("pubkey") or signal.extra.get("public_key")
        if pk and sig and content:
            verified = verify_ed25519(pk, content, sig)
    rec["verified"] = verified

    if prof.get("require_verified") and not verified:
        raise HTTPException(status_code=403, detail="Signature required for this source")

    # Persist
    _append_log(rec)

    # Fan-out to SSE subscribers
    for q in list(SUBSCRIBERS):
        try: q.put_nowait({"type": "breath_signal", "record": rec})
        except Exception: pass

    # Optional: Supabase
    if supabase:
        try:
            supabase.table("breath_signals").insert(rec).execute()
        except Exception as e:
            print(f"⚠️ Supabase insert failed: {e}")

    # Also store as a JSON artifact in inbox (optional for DC reconciliation)
    ts = signal.timestamp or rec["received_at"].replace(":", "-")
    src = signal.source.replace("/", "-")
    (INBOX_DIR / f"{ts}_{src}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")

    return {"ok": True, "stored": True, "weight": rec["weight"], "verified": rec["verified"]}

# Optional: tiny DAG runner hook (kept minimal; can expand later)
@app.post("/run")
async def run_plan(authorization: Optional[str] = Header(None)):
    if not _auth_ok(authorization):
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"ok": True, "message": "Runner stub active"}