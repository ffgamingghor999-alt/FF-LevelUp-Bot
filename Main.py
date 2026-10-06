import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List

from dashboard_server import create_app

ROOT = Path(__file__).resolve().parent
ACCOUNT_FILE = ROOT / "accounts.json"
DEVICE_FILE = ROOT / "devices.json"
TOKEN_CACHE_FILE = ROOT / "token_cache.json"
TEMPLATE_FILE = ROOT / "templates" / "index.html"

START_MATCH_INTERVAL = 3.0
NEW_MATCH_DELAY = 3.0
MAX_MATCH_DURATION = 700
PRIORITY_REGIONS = ["BD", "IND", "SG", "TH", "MY"]
WEB_PORT = 20335


def load_json(path: Path, default: Any):
    if not path.exists():
        path.write_text(json.dumps(default, indent=2), encoding="utf-8")
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, payload: Any):
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


async def bootstrap_files():
    accounts = load_json(
        ACCOUNT_FILE,
        [
            {"uid": "sample_uid_001", "password": "sample_password_001"},
            {"uid": "sample_uid_002", "password": "sample_password_002"},
        ],
    )
    devices = load_json(
        DEVICE_FILE,
        {
            "sample_uid_001": {
                "device_id": "device-001",
                "device_name": "Pixel-7",
                "region": "BD",
                "last_seen": "2026-01-01T00:00:00Z",
            },
            "sample_uid_002": {
                "device_id": "device-002",
                "device_name": "Galaxy-A54",
                "region": "IND",
                "last_seen": "2026-01-01T00:00:00Z",
            },
        },
    )
    token_cache = load_json(TOKEN_CACHE_FILE, {})
    save_json(ACCOUNT_FILE, accounts)
    save_json(DEVICE_FILE, devices)
    save_json(TOKEN_CACHE_FILE, token_cache)


async def simulate_match(account: Dict[str, Any], region: str):
    uid = str(account.get("uid", "unknown"))
    exp_gain = 125 + (len(uid) % 75)
    match_duration = 180 + (len(uid) % 160)
    return {
        "uid": uid,
        "region": region,
        "exp_gain": exp_gain,
        "match_duration": match_duration,
        "status": "simulated",
    }


async def run_simulation_loop(global_state: Dict[str, Any]):
    while True:
        accounts = load_json(ACCOUNT_FILE, [])
        devices = load_json(DEVICE_FILE, {})
        for account in accounts:
            uid = str(account.get("uid", "unknown"))
            region = PRIORITY_REGIONS[(len(uid) + len(global_state["tick"])) % len(PRIORITY_REGIONS)]
            if uid not in devices:
                devices[uid] = {
                    "device_id": f"device-{uid[-4:]}",
                    "device_name": "Simulated Device",
                    "region": region,
                    "last_seen": "now",
                }
            match_result = await simulate_match(account, region)
            global_state["accounts"].append(
                {
                    "uid": uid,
                    "level": 8 + (len(uid) % 11),
                    "exp": 2100 + (match_result["exp_gain"] * 8),
                    "region": region,
                    "matches_played": 1,
                    "exp_gain": match_result["exp_gain"],
                    "last_match": match_result["match_duration"],
                }
            )
            global_state["logs"].append(
                f"[{uid}] simulated match complete in {region} | +{match_result['exp_gain']} EXP"
            )
        save_json(DEVICE_FILE, devices)
        global_state["tick"] += 1
        await asyncio.sleep(START_MATCH_INTERVAL)


async def main():
    await bootstrap_files()

    state = {
        "accounts": [],
        "logs": [
            "TEAM 84FF - FreeFire Account Dashboard (Safe Demo)",
            "Web Dashboard live at http://localhost:20335",
        ],
        "tick": 0,
    }

    app = create_app(state)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", WEB_PORT)
    await site.start()
    print("TEAM 84FF - FreeFire Account Dashboard (Safe Demo)")
    print(f"Web Dashboard live at http://localhost:{WEB_PORT}")

    asyncio.create_task(run_simulation_loop(state))
    await asyncio.Event().wait()


if __name__ == "__main__":
    import aiohttp.web as web

    asyncio.run(main())
