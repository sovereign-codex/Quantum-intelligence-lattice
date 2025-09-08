import os, aiofiles, datetime, json

ART_DIR = os.environ.get("QIL_ART_DIR", "artifacts")

async def run(vot, ctx):
    # Stub: generate offline-first page scaffold (no styling)
    os.makedirs(ART_DIR, exist_ok=True)
    day = vot["Day"]
    path = os.path.join(ART_DIR, f"day{day:03d}_codexnet.html")
    html = f"""<!doctype html>
<html><head><meta charset='utf-8'><title>CodexNet Offline</title></head>
<body>
<h1>CodexNet – Offline First</h1>
<p>Generated: {datetime.datetime.utcnow().isoformat()}</p>
<ul>
  <li>Theme: {vot['Theme']}</li>
  <li>VOT: {vot['VOT Name']}</li>
  <li>Deliverable: {vot['Primary Deliverable']}</li>
</ul>
</body></html>"""
    async with aiofiles.open(path, "w") as f:
        await f.write(html)
        from app.infra.storage_supabase import upload_file
    url = upload_file(path)
    return {"files_created": 1, "artifact_url": url, "html_bytes": len(html)}
