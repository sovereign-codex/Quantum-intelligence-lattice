import os, aiofiles, datetime

ART_DIR = os.environ.get("QIL_ART_DIR", "artifacts")

async def run(vot, ctx):
    os.makedirs(ART_DIR, exist_ok=True)
    day = vot["Day"]
    path = os.path.join(ART_DIR, f"day{day:03d}_water_test_results.txt")
    results = f"""Waterwright Report
Date: {datetime.datetime.utcnow().isoformat()}
Cold plasma desalination test parameters and results.
"""
    async with aiofiles.open(path, "w") as f:
        await f.write(results)
    from app.infra.storage_supabase import upload_file
    url = upload_file(path)
    return {"files_created": 1, "artifact_url": url}
