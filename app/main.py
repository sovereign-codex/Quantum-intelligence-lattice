import os, asyncio, argparse
from fastapi import FastAPI
from app.orchestrator import Orchestrator

CSV_PATH = os.environ.get("QIL_CSV", "data/QIL_365_VOT_Metrics_Plan.csv")

app = FastAPI(title="QIL – VOT Orchestrator")

orch: Orchestrator | None = None
task = None

@app.post("/start")
async def start(concurrency: int = 32):
    global orch, task
    orch = Orchestrator(CSV_PATH, concurrency=concurrency)
    orch.load()
    task = asyncio.create_task(orch.run())
    return {"status": "started", "concurrency": concurrency}

@app.get("/status")
async def status():
    if orch:
        return orch.status_counts()
    return {"total": 0, "done": 0, "open": 0}

@app.post("/stop")
async def stop():
    global orch, task
    if task:
        task.cancel()
    return {"status": "stopping"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cli", action="store_true")
    parser.add_argument("--concurrency", type=int, default=16)
    args = parser.parse_args()
    if args.cli:
        o = Orchestrator(CSV_PATH, concurrency=args.concurrency)
        o.load()
        asyncio.run(o.run())
        print(o.status_counts())
    else:
        import uvicorn
        uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
