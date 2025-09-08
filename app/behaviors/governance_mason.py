import os, aiofiles, datetime

ART_DIR = os.environ.get("QIL_ART_DIR", "artifacts")

async def run(vot, ctx):
    os.makedirs(ART_DIR, exist_ok=True)
    day = vot["Day"]
    path = os.path.join(ART_DIR, f"day{day:03d}_governance_outline.txt")
    outline = f"""Governance Mason Draft
Date: {datetime.datetime.utcnow().isoformat()}
Outline for Sovereign Intelligence Research Institute legal structure.
"""
    async with aiofiles.open(path, "w") as f:
        await f.write(outline)
    from app.infra.storage_supabase import upload_file
    url = upload_file(path)
    return {"files_created": 1, "artifact_url": url}
