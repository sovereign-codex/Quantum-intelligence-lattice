import os, json, uuid, time
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory, abort

APP_NAME = "Quantum Intelligence Lattice"
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
SIGNALS_PATH = DATA_DIR / "signals.json"
MAX_SIGNALS = 500  # keep the file compact

# load existing signals (if any)
def load_signals():
    if SIGNALS_PATH.exists():
        try:
            return json.loads(SIGNALS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_signals(rows):
    # trim to last N
    rows = rows[-MAX_SIGNALS:]
    SIGNALS_PATH.write_text(json.dumps(rows, indent=2), encoding="utf-8")

signals = load_signals()

app = Flask(__name__)

@app.get("/")
def index():
    # most recent first
    rows = sorted(signals, key=lambda r: r.get("received_at", ""), reverse=True)
    return render_template("index.html", app_name=APP_NAME, signals=rows)

@app.get("/health")
def health():
    return {"ok": True, "count": len(signals)}

@app.post("/api/signal")
def api_signal():
    """
    Expected JSON payload from Dream Console Actions:
      { "source": "dream-console", "status": "breath complete",
        "file": "codex/cycle_XXX.md", "timestamp": "2025-09-07T12:34:56Z" }

    Optional simple shared-secret check:
      header: X-QIL-Secret: <value>   (must match env QIL_WEBHOOK_SECRET if set)
    """
    secret_expected = os.getenv("QIL_WEBHOOK_SECRET", "").strip()
    if secret_expected:
        if request.headers.get("X-QIL-Secret", "").strip() != secret_expected:
            abort(401)

    try:
        payload = request.get_json(force=True, silent=False) or {}
    except Exception as e:
        return jsonify({"ok": False, "error": f"bad json: {e}"}), 400

    row = {
        "id": str(uuid.uuid4()),
        "source": payload.get("source", "unknown"),
        "status": payload.get("status", "unknown"),
        "file": payload.get("file", ""),
        "timestamp": payload.get("timestamp", ""),
        "received_at": datetime.now(timezone.utc).isoformat(),
        "ua": request.headers.get("User-Agent", ""),
    }
    signals.append(row)
    save_signals(signals)
    return {"ok": True, "stored": row["id"]}

# simple static (optional)
@app.get("/static/<path:path>")
def static_files(path):
    return send_from_directory("static", path)

if __name__ == "__main__":
    # Replit usually sets PORT
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)