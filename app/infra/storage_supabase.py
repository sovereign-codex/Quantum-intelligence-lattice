import os, datetime
from typing import Optional

try:
    from supabase import create_client
except Exception:
    create_client = None

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
QIL_BUCKET = os.environ.get("QIL_BUCKET", "artifacts")
QIL_PUBLIC_URL = os.environ.get("QIL_PUBLIC_URL")  # optional CDN/public base

_client = None

def client():
    global _client
    if _client is None:
        if not (SUPABASE_URL and SUPABASE_KEY):
            raise RuntimeError("Supabase env missing")
        if create_client is None:
            raise RuntimeError("supabase-py not installed")
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client

def upload_file(local_path: str, dest_prefix: str = "artifacts") -> Optional[str]:
    sb = client()
    name = os.path.basename(local_path)
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    key = f"{dest_prefix}/{ts}_{name}"
    with open(local_path, "rb") as f:
        sb.storage.from_(QIL_BUCKET).upload(key, f, {"contentType": _guess_ct(name)}, upsert=True)
    # Try to get public URL
    if QIL_PUBLIC_URL:
        return f"{QIL_PUBLIC_URL}/{key}"
    # Fallback to signed URL (valid 7 days)
    try:
        signed = sb.storage.from_(QIL_BUCKET).create_signed_url(key, 7*24*3600)
        return signed.get("signedURL") or signed.get("signed_url")
    except Exception:
        # last resort: public URL method (if bucket public)
        try:
            pub = sb.storage.from_(QIL_BUCKET).get_public_url(key)
            return pub
        except Exception:
            return None

def _guess_ct(name: str) -> str:
    lower = name.lower()
    if lower.endswith(".html"): return "text/html"
    if lower.endswith(".md"): return "text/markdown"
    if lower.endswith(".txt"): return "text/plain"
    if lower.endswith(".json"): return "application/json"
    return "application/octet-stream"
