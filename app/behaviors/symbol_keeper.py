import os, aiofiles, datetime

ART_DIR = os.environ.get("QIL_ART_DIR", "artifacts")

async def run(vot, ctx):
    os.makedirs(ART_DIR, exist_ok=True)
    day = vot["Day"]
    path = os.path.join(ART_DIR, f"day{day:03d}_symbol_notes.txt")
    content = f"""Symbol Keeper Notes
Timestamp: {datetime.datetime.utcnow().isoformat()}
Role: Symbol Keeper
Deliverable: {vot['Primary Deliverable']}
Outline: Steps to design and integrate symbolic elements.
"""
    async with aiofiles.open(path, "w") as f:
        await f.write(content)
    from app.infra.storage_supabase import upload_file
    url = upload_file(path)
    return {"files_created": 1, "artifact_url": url}
