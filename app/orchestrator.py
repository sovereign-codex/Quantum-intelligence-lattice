# app/orchestrator.py
# -----------------------------------------------------------------------------
# Orchestrator + FastAPI webhook entrypoint for the Quantum Intelligence Lattice
# -----------------------------------------------------------------------------

import os
import csv
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict

# Optional imports from your repo; safe fallbacks if not present
try:
    # expected: async def submit_job(task: Dict[str, Any]) -> Dict[str, Any]
    from app.worker import submit_job  # type: ignore
except Exception:
    async def submit_job(task: Dict[str, Any]) -> Dict[str, Any]:  # fallback
        # Minimal no-op worker: pretend to do the work
        await asyncio.sleep(0.1)
        return {"status": "ok", "task": task.get("Task")}

try:
    # optional infra module (e.g., db clients, logging)
    from app.infra import db  # type: ignore  # noqa: F401
except Exception:
    db = None  # noqa: F401


# =============================================================================
# Core Orchestrator
# =============================================================================
class Orchestrator:
    """
    Very small DAG-like orchestrator driven by a CSV plan.

    CSV expected headers (case-insensitive):
      - Day (int or str id)
      - Task (str)
      - DependsOn (comma-separated list of Day ids)  [optional]
      - Payload (json or plain text)                 [optional]
    """

    def __init__(self, csv_path: str = "data/QIL_plan.csv", concurrency: int = 3):
        self.csv_path = csv_path
        self.concurrency = max(1, int(concurrency))
        self.graph: Dict[str, List[str]] = defaultdict(list)   # parent -> [children]
        self.deps_left: Dict[str, int] = {}                    # node -> deps remaining
        self.rows: Dict[str, Dict[str, Any]] = {}              # node -> row dict
        self.started: Dict[str, bool] = {}
        self.completed: Dict[str, bool] = {}
        self.stop_flag = False

    # ----------------------------
    # Loading & graph construction
    # ----------------------------
    def load(self) -> None:
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"Plan not found: {self.csv_path}")

        self.graph.clear()
        self.deps_left.clear()
        self.rows.clear()
        self.started.clear()
        self.completed.clear()

        def norm(s: str) -> str:
            return (s or "").strip()

        with open(self.csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            # Normalize header names
            headers = {h.lower(): h for h in reader.fieldnames or []}
            h_day = headers.get("day") or headers.get("id") or "Day"
            h_task = headers.get("task") or "Task"
            h_dep = headers.get("dependson") or headers.get("deps") or "DependsOn"
            h_payload = headers.get("payload") or "Payload"

            for row in reader:
                node = norm(str(row.get(h_day, "")))
                if not node:
                    # skip blank row
                    continue
                task_name = norm(row.get(h_task, ""))
                deps_raw = norm(row.get(h_dep, ""))
                payload_raw = row.get(h_payload, "")

                # parse optional JSON payload
                payload: Any
                try:
                    payload = json.loads(payload_raw) if payload_raw else None
                except Exception:
                    payload = payload_raw  # accept plaintext fallback

                self.rows[node] = {
                    "Day": node,
                    "Task": task_name,
                    "DependsOn": deps_raw,
                    "Payload": payload,
                }
                self.started[node] = False
                self.completed[node] = False

        # Build dependencies
        for node, data in self.rows.items():
            deps_list = [d.strip() for d in (data.get("DependsOn") or "").split(",") if d.strip()]
            self.deps_left[node] = len(deps_list)
            for parent in deps_list:
                self.graph[parent].append(node)

    def ready_nodes(self) -> List[str]:
        return [
            n for n in self.rows
            if not self.started[n] and self.deps_left.get(n, 0) == 0
        ]

    def mark_done(self, node: str) -> None:
        if self.completed.get(node):
            return
        self.completed[node] = True
        for child in self.graph.get(node, []):
            self.deps_left[child] = max(0, self.deps_left.get(child, 0) - 1)

    # ----------------------------
    # Runner
    # ----------------------------
    async def _run_node(self, node: str, sem: asyncio.Semaphore) -> None:
        async with sem:
            self.started[node] = True
            task_row = self.rows[node]
            try:
                result = await submit_job(task_row)
                # You can persist result via db or files here
                _ = result
            except Exception as e:
                # If a task fails, we *do not* unlock its children
                # (simple policy; adjust as needed)
                print(f"✖ Task failed [{node} - {task_row.get('Task')}]: {e}")
                return
            finally:
                self.mark_done(node)
                print(f"✔ Task complete [{node}]")

    async def run(self) -> None:
        if not self.rows:
            self.load()
        sem = asyncio.Semaphore(self.concurrency)

        pending: Dict[str, asyncio.Task] = {}

        while not self.stop_flag:
            # schedule any ready nodes
            for node in self.ready_nodes():
                if node not in pending:
                    pending[node] = asyncio.create_task(self._run_node(node, sem))

            if not pending:
                # No work left (either completed or blocked)
                break

            # Wait for any task to finish then loop to schedule next
            done, _ = await asyncio.wait(pending.values(), return_when=asyncio.FIRST_COMPLETED)
            # Drop finished tasks from pending
            for t in list(pending.keys()):
                if pending[t] in done:
                    del pending[t]

        print("🏁 Orchestration loop finished.")


# =============================================================================
# FastAPI Ingress (Webhook)
# =============================================================================
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

# Optional Supabase (if you’ve configured env vars)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"⚠️ Supabase init failed: {e}")

QIL_SECRET = os.getenv("QIL_SECRET")  # set in Replit Secrets
INBOX_DIR = Path("data/inbox")
INBOX_DIR.mkdir(parents=True, exist_ok=True)

# Where your CSV plan lives (can be set via env)
CSV_PLAN = os.getenv("QIL_PLAN_CSV", "data/QIL_plan.csv")
CONCURRENCY = int(os.getenv("QIL_CONCURRENCY", "3"))

# Single orchestrator instance
_orch = Orchestrator(csv_path=CSV_PLAN, concurrency=CONCURRENCY)

app = FastAPI(title="QIL Orchestrator", version="0.1.0")


class TaskIn(BaseModel):
    source: str
    status: str
    file: str
    timestamp: str
    note: Optional[str] = None


def _auth_ok(request: Request) -> bool:
    expected = f"Bearer {QIL_SECRET}" if QIL_SECRET else None
    provided = request.headers.get("Authorization")
    return bool(expected) and (provided == expected)


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.post("/ingest")
async def ingest(task: TaskIn, request: Request):
    # Secret gate
    if not _auth_ok(request):
        raise HTTPException(status_code=403, detail="Forbidden")

    # persist inbound signal
    out = INBOX_DIR / f"{task.timestamp}_{task.source}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(task.dict(), f, indent=2)

    # optional: log to supabase
    if supabase:
        try:
            supabase.table("qil_tasks").insert(task.dict()).execute()
        except Exception as e:
            print(f"⚠️ Supabase log failed: {e}")

    return {"message": "Task ingested", "file": str(out)}


@app.post("/run")
async def run_plan(request: Request):
    # Secret gate
    if not _auth_ok(request):
        raise HTTPException(status_code=403, detail="Forbidden")

    # Load & run the plan
    try:
        _orch.load()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    await _orch.run()
    return {
        "message": "Plan executed",
        "csv": _orch.csv_path,
        "completed": sum(1 for v in _orch.completed.values() if v),
        "total": len(_orch.rows),
    }


# =============================================================================
# Local dev entry point (Replit/uvicorn)
# =============================================================================
if __name__ == "__main__":
    # Allow running: python app/orchestrator.py
    try:
        import uvicorn
        uvicorn.run("app.orchestrator:app", host="0.0.0.0", port=8080, reload=False)
    except Exception as e:
        print(f"Run with uvicorn failed: {e}")
        print("Try: uvicorn app.orchestrator:app --host 0.0.0.0 --port 8080")
