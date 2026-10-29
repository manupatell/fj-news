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
    print("ERROR: DISCORD_WEBHOOK environment variable is missing.")
    raise SystemExit(1)


def load_state():
    if not STATE.exists():
        return {"last_guid": 0}

    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"last_guid": 0}


def save_state(last_guid):
    STATE.write_text(
        json.dumps({"last_guid": last_guid}, indent=2),
        encoding="utf-8",
    )


def get_title(headline: str):
    text = headline.upper()

    if "CPI" in text:
        return "🔴 CPI RELEASE"

    if "PPI" in text:
        return "🔴 PPI RELEASE"

    if "NFP" in text or "NONFARM" in text:
        return "🔴 NONFARM PAYROLLS"

    if "FOMC" in text:
        return "🔴 FOMC"

    if "POWELL" in text:
        return "🟠 POWELL SPEECH"

    if "GDP" in text:
        return "🔴 GDP"

    if "PCE" in text:
        return "🔴 PCE"

    if "PMI" in text:
        return "🟠 PMI"

    if "BREAKING" in text:
        return "🚨 BREAKING NEWS"

    return "🚨 HIGH IMPACT NEWS"


state = load_state()
last_guid = state["last_guid"]

data = json.loads(LATEST.read_text(encoding="utf-8"))
items = list(reversed(data["items"]))  # oldest → newest

highest_guid = last_guid

for item in items:

    guid = item.get("guid") or 0

    if guid <= last_guid:
        continue

    headline = item["headline"]

    ok, color = is_high_impact(headline)

    highest_guid = max(highest_guid, guid)

    if not ok:
        continue

    embed = {
        "title": get_title(headline),
        "description": headline,
        "color": color,
        "footer": {
            "text": "FinancialJuice RSS"
        },
    }

    ts = item.get("ts")
    if ts:
        embed["timestamp"] = ts

    payload = {
        "embeds": [embed]
    }

    try:
        response = requests.post(
            WEBHOOK,
            json=payload,
            timeout=20,
        )

        print(
            f"[{response.status_code}] {headline}"
        )

    except Exception as e:
        print(e)

    time.sleep(1)

save_state(highest_guid)

print("Finished Discord notifications.")
