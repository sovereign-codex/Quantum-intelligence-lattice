import os, aiofiles, datetime

ART_DIR = os.environ.get("QIL_ART_DIR", "artifacts")

async def run(vot, ctx):
    # Stub: assemble Codex preface snapshot
    os.makedirs(ART_DIR, exist_ok=True)
    day = vot["Day"]
    path = os.path.join(ART_DIR, f"day{day:03d}_codex_herald.md")
    content = f"""# Garden Flame Codex – Preface (Auto Snapshot)
Timestamp: {datetime.datetime.utcnow().isoformat()}

Axioms:
- Your greatest achievement will always be remembering who you are.
- Fractal Law of Surrendered Sovereignty.

Deliverable: {vot['Primary Deliverable']}
"""
    async with aiofiles.open(path, "w") as f:
        await f.write(content)
        from app.infra.storage_supabase import upload_file
    url = upload_file(path)
    return {"files_created": 1, "artifact_url": url, "sections": 2}
