import os, csv, argparse
from supabase import create_client

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True, help="Path to QIL_365_VOT_Metrics_Plan.csv")
    p.add_argument("--url", required=True)
    p.add_argument("--key", required=True)
    args = p.parse_args()

    sb = create_client(args.url, args.key)

    with open(args.csv) as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            day = int(r["Day"])
            role = (r["VOT Name"].split(" – ")[0]).strip()
            theme = r["Theme"]
            rows.append({"day": day, "role": role, "theme": theme})

    # Upsert in batches
    for i in range(0, len(rows), 200):
        batch = rows[i:i+200]
        sb.table("vot").upsert(batch, on_conflict="day").execute()

    print(f"Upserted {len(rows)} rows into vot")

if __name__ == "__main__":
    main()
