import importlib, os

async def submit_job(vot_row: dict, ctx: dict) -> (bool, dict):
    # vot_row['VOT Name'] is like 'Codex Herald – Day 1'
    role = vot_row.get("VOT Name", "").split(" – ")[0] or "generic"
    module_name = role.lower().replace(" ", "_")
    try:
        mod = importlib.import_module(f"app.behaviors.{module_name}")
    except Exception:
        # fallback to generic behavior
        mod = importlib.import_module("app.behaviors.generic")
    try:
        metrics = await mod.run(vot_row, ctx)
        return True, metrics or {}
    except Exception as e:
        return False, {"error": str(e)}
