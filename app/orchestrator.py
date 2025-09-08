import os, csv, asyncio, datetime, json
from collections import defaultdict
from typing import Dict, Any
from app.worker import submit_job
from app.infra import db

class Orchestrator:
    def __init__(self, csv_path: str, concurrency: int = 32):
        self.csv_path = csv_path
        self.concurrency = concurrency
        self.graph = defaultdict(list)   # parent -> [children]
        self.deps_left = {}              # day -> count
        self.rows: Dict[int, Dict[str, Any]] = {}
        self.stop_flag = False

    def load(self):
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(self.csv_path)
        with open(self.csv_path) as f:
            for row in csv.DictReader(f):
                day = int(row["Day"])
                deps = [int(x) for x in row["Dependencies (Day #)"].split(",") if x.strip().isdigit()]
                self.rows[day] = row
                self.deps_left[day] = len(deps)
                for d in deps:
                    self.graph[d].append(day)

    async def run(self):
        db.init_db()
        ready = asyncio.Queue()
        # seed ready
        for day, left in self.deps_left.items():
            if left == 0:
                await ready.put(day)

        async def worker_loop(i: int):
            while not self.stop_flag:
                day = await ready.get()
                row = self.rows[day]
                run_id = db.start_run(day)
                ok, metrics = await submit_job(row, ctx={"worker": i})
                db.finish_run(run_id, ok, metrics)
                # add simple metric example
                for k, v in metrics.items():
                    try:
                        db.add_metric(day, k, float(v))
                    except Exception:
                        pass
                # unlock children
                for child in self.graph[day]:
                    self.deps_left[child] -= 1
                    if self.deps_left[child] == 0:
                        await ready.put(child)

        workers = [asyncio.create_task(worker_loop(i)) for i in range(self.concurrency)]
        # wait for exhaustion: when queue empties and all deps resolved
        while True:
            await asyncio.sleep(0.5)
            if all(v == 0 for v in self.deps_left.values()) and ready.empty():
                self.stop_flag = True
                break
        for w in workers:
            w.cancel()

    def status_counts(self):
        total = len(self.rows)
        # naive: pull counts from DB run table
        try:
            import sqlite3
            conn = sqlite3.connect(os.environ.get("QIL_DB", "qil.db"))
            cur = conn.cursor()
            cur.execute("SELECT COUNT(1) FROM run WHERE ok=1")
            done = cur.fetchone()[0]
        except Exception:
            done = 0
        return {"total": total, "done": done, "open": total - done}
