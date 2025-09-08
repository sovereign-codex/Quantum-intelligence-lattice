
import os, sys, argparse, csv, json, time
from supabase import create_client

def run_sql(sb, sql: str):
    # supabase-py doesn't execute raw SQL directly; we rely on a PostgREST RPC workaround or ask the user to paste SQL.
    # To keep this script self-contained, we will populate tables via insert/upsert and skip direct SQL execution.
    # For initial setup, please run schema.sql in the Supabase SQL editor once.
    print("[note] Please run schema.sql in the Supabase SQL editor to create tables & RLS before running this script.")

def ensure_bucket(sb, bucket: str, public_url: str | None):
    try:
        buckets = sb.storage.list_buckets()
        names = [b["name"] for b in buckets]
        if bucket not in names:
            sb.storage.create_bucket(bucket, {"public": bool(public_url)})
            print(f"[ok] Created bucket: {bucket} (public={bool(public_url)})")
        else:
            print(f"[ok] Bucket exists: {bucket}")
    except Exception as e:
        print("[warn] Could not verify/create bucket:", e)

def upsert_vot(sb, csv_path: str):
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            day = int(r["Day"])
            role = (r["VOT Name"].split(" – ")[0]).strip()
            theme = r["Theme"]
            rows.append({"day": day, "role": role, "theme": theme})
    for i in range(0, len(rows), 200):
        sb.table("vot").upsert(rows[i:i+200], on_conflict="day").execute()
    print(f"[ok] Upserted {len(rows)} rows into vot")

def upsert_edges(sb, csv_path: str):
    edges = []
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            day = int(row["Day"])
            deps = [int(x) for x in row["Dependencies (Day #)"].split(",") if x.strip().isdigit()]
            for d in deps:
                edges.append({"src": d, "dst": day})
    for i in range(0, len(edges), 400):
        sb.table("edge").upsert(edges[i:i+400]).execute()
    print(f"[ok] Upserted {len(edges)} edges into edge")

def main():
    p = argparse.ArgumentParser(description="QIL one-click Supabase init")
    p.add_argument("--csv", required=True, help="Path to QIL_365_VOT_Metrics_Plan.csv")
    p.add_argument("--url", default=os.getenv("SUPABASE_URL"))
    p.add_argument("--key", default=os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
    p.add_argument("--bucket", default=os.getenv("QIL_BUCKET", "artifacts"))
    p.add_argument("--public_url", default=os.getenv("QIL_PUBLIC_URL"))
    args = p.parse_args()
    if not args.url or not args.key:
        print("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)
    sb = create_client(args.url, args.key)

    # 1) (Manual once) Run schema.sql in Supabase SQL editor (cannot run raw SQL via supabase-py v2)
    run_sql(sb, open("schema.sql").read())

    # 2) Ensure artifacts bucket exists
    ensure_bucket(sb, args.bucket, args.public_url)

    # 3) Ingest vot + edge from CSV
    upsert_vot(sb, args.csv)
    upsert_edges(sb, args.csv)

    print("[done] Supabase init completed.")

if __name__ == "__main__":
    main()
