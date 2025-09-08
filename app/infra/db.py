import sqlite3, json, os, datetime
from typing import Dict, Any

DB_PATH = os.environ.get("QIL_DB", "qil.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS run (id INTEGER PRIMARY KEY AUTOINCREMENT, day INTEGER, ok INTEGER, started_at TEXT, finished_at TEXT, artifacts TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS metric (id INTEGER PRIMARY KEY AUTOINCREMENT, day INTEGER, k TEXT, v REAL, ts TEXT)")
    conn.commit()
    conn.close()

def start_run(day: int) -> int:
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.datetime.utcnow().isoformat()
    cur.execute("INSERT INTO run(day, ok, started_at, finished_at, artifacts) VALUES(?,?,?,?,?)",
                (day, None, now, None, "{}"))
    rid = cur.lastrowid
    conn.commit()
    conn.close()
    return rid

def finish_run(run_id: int, ok: bool, artifacts: Dict[str, Any] = {}):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.datetime.utcnow().isoformat()
    cur.execute("UPDATE run SET ok=?, finished_at=?, artifacts=? WHERE id=?",
                (1 if ok else 0, now, json.dumps(artifacts), run_id))
    conn.commit()
    conn.close()

def add_metric(day: int, k: str, v: float):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.datetime.utcnow().isoformat()
    cur.execute("INSERT INTO metric(day, k, v, ts) VALUES(?,?,?,?)", (day, k, v, now))
    conn.commit()
    conn.close()
