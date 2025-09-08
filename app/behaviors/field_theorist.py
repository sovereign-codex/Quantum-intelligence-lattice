import os, aiofiles, datetime

ART_DIR = os.environ.get("QIL_ART_DIR", "artifacts")

async def run(vot, ctx):
    os.makedirs(ART_DIR, exist_ok=True)
    day = vot["Day"]
    path = os.path.join(ART_DIR, f"day{day:03d}_field_theory.txt")
    theory = f"""Field Theorist Log
Date: {datetime.datetime.utcnow().isoformat()}
Hypothesis refinement for Etheron Field.
"""
    async with aiofiles.open(path, "w") as f:
        await f.write(theory)
    from app.infra.storage_supabase import upload_file
    url = upload_file(path)
    return {"files_created": 1, "artifact_url": url}
