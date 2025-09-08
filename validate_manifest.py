import json
import os
import requests
from datetime import datetime

REQUIRED_FIELDS = {"id", "name", "type", "url", "description", "status"}
MANIFEST_PATH = os.path.join("manifest", "nodes.json")
HEARTBEAT_PATH = os.path.join("manifest", "heartbeat.json")

def validate_structure(node):
    missing = REQUIRED_FIELDS - node.keys()
    if missing:
        return f"❌ Missing fields {missing} in node {node.get('id','?')}"
    return None

def check_url(url):
    try:
        r = requests.head(url, allow_redirects=True, timeout=5)
        if r.status_code < 400:
            return None
        return f"⚠️ URL {url} returned status {r.status_code}"
    except Exception as e:
        return f"⚠️ Could not resolve {url}: {e}"

def write_heartbeat(count, errors):
    hb = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "nodes_checked": count,
        "status": "healthy" if not errors else "issues",
        "errors": errors
    }
    with open(HEARTBEAT_PATH, "w", encoding="utf-8") as f:
        json.dump(hb, f, indent=2)
    print("💓 Heartbeat written:", HEARTBEAT_PATH)

def main():
    if not os.path.exists(MANIFEST_PATH):
        print(f"❌ Manifest file not found at {MANIFEST_PATH}")
        return

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data.get("nodes", [])
    print(f"Validating {len(nodes)} nodes...")

    errors = []
    for node in nodes:
        # structure
        err = validate_structure(node)
        if err: errors.append(err)

        # url
        url_err = check_url(node["url"])
        if url_err: errors.append(url_err)

    if not errors:
        print("✅ Manifest looks good -- all nodes valid and URLs resolve.")
    else:
        print("Found issues:")
        for e in errors:
            print(" -", e)

    write_heartbeat(len(nodes), errors)

if __name__ == "__main__":
    main()