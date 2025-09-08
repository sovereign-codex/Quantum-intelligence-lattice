import os, aiofiles, datetime

ART_DIR = os.environ.get("QIL_ART_DIR", "artifacts")

async def run(vot, ctx):
    os.makedirs(ART_DIR, exist_ok=True)
    day = vot["Day"]
    path = os.path.join(ART_DIR, f"day{day:03d}_narrative.txt")
    text = f"""[{datetime.datetime.utcnow().isoformat()}] Narrative Outline
Role: Narrative Weaver
Deliverable: {vot['Primary Deliverable']}
Themes: {vot['Theme']}
This file contains an outline for public resonance storytelling.
"""
    async with aiofiles.open(path, "w") as f:
        await f.write(text)
    from app.infra.storage_supabase import upload_file
    url = upload_file(path)
    return {"files_created": 1, "artifact_url": url}
