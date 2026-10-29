import json
import os
import time
from pathlib import Path

import requests

from filters import is_high_impact

HERE = Path(__file__).parent
LATEST = HERE / "latest.json"
STATE = HERE / "state.json"

WEBHOOK = os.environ.get("DISCORD_WEBHOOK")

if not WEBHOOK:
    print("DISCORD_WEBHOOK not found.")
    raise SystemExit()


def load_state():
    if not STATE.exists():
        return {"last_guid": 0}

    try:
        return json.loads(STATE.read_text())
    except:
        return {"last_guid": 0}


def save_state(last_guid):
    STATE.write_text(
        json.dumps(
            {
                "last_guid": last_guid
            },
            indent=2,
        )
    )


state = load_state()
last_guid = state["last_guid"]

with open(LATEST, "r", encoding="utf8") as f:
    data = json.load(f)

items = data["items"]

# oldest -> newest
items.reverse()

highest_guid = last_guid

for item in items:

    guid = item.get("guid") or 0

    if guid <= last_guid:
        continue

    headline = item["headline"]

    ok, color = is_high_impact(headline)

    if not ok:
        highest_guid = max(highest_guid, guid)
        continue

    ts = item.get("ts")

    embed = {
        "title": "🚨 HIGH IMPACT BREAKING",
        "description": headline,
        "color": color,
        "footer": {
            "text": "FinancialJuice"
        },
        "timestamp": ts
    }

    payload = {
        "embeds": [embed]
    }

    r = requests.post(
        WEBHOOK,
        json=payload,
        timeout=20,
    )

    print(
        guid,
        headline,
        r.status_code,
    )

    highest_guid = max(highest_guid, guid)

    time.sleep(0.8)

save_state(highest_guid)

print("Done.")
