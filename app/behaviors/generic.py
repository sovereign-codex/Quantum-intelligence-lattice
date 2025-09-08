import os, aiofiles, datetime

ART_DIR = os.environ.get("QIL_ART_DIR", "artifacts")

async def run(vot, ctx):
    os.makedirs(ART_DIR, exist_ok=True)
    day = vot["Day"]
    name = vot["VOT Name"]
    deliverable = vot["Primary Deliverable"]
    path = os.path.join(ART_DIR, f"day{day:03d}_generic.txt")
    async with aiofiles.open(path, "w") as f:
        await f.write(f"[{datetime.datetime.utcnow().isoformat()}] AUTO DRAFT\n{name}\nDeliverable: {deliverable}\n")
        from app.infra.storage_supabase import upload_file
    url = upload_file(path)
    return {"files_created": 1, "artifact_url": url}
