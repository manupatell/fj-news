import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from filters import is_high_impact

HERE = Path(__file__).parent
LATEST = HERE / "latest.json"
STATE = HERE / "state.json"

WEBHOOK = os.environ.get("DISCORD_WEBHOOK")

# Real-time guard: never post a headline published more than this many
# minutes ago, even if its GUID is "unseen" (lost state, failed push, etc.)
MAX_AGE_MIN = int(os.environ.get("DISCORD_MAX_AGE_MIN", "15"))

if not WEBHOOK:
    print("ERROR: DISCORD_WEBHOOK environment variable is missing.")
    raise SystemExit(1)


def load_state():
    if not STATE.exists():
        return {"last_guid": 0}

    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
        state["last_guid"] = int(state.get("last_guid") or 0)
        return state
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


def age_minutes(item):
    """Minutes since the headline was published (falls back to ingested)."""
    raw = item.get("ts") or item.get("ingested")
    if not raw:
        return 0.0
    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds() / 60
    except ValueError:
        return 0.0


def post(payload):
    """POST to Discord. Retries on 429. Returns True if delivered."""
    for _ in range(3):
        response = requests.post(WEBHOOK, json=payload, timeout=20)

        if response.status_code == 429:
            try:
                wait = float(response.json().get("retry_after", 2))
            except Exception:
                wait = 2.0
            print(f"[429] rate limited, waiting {wait:.1f}s")
            time.sleep(wait + 0.5)
            continue

        print(f"[{response.status_code}]")
        return 200 <= response.status_code < 300

    return False


data = json.loads(LATEST.read_text(encoding="utf-8"))
items = list(reversed(data["items"]))  # oldest → newest

state = load_state()
last_guid = state["last_guid"]

# First run / lost state: do NOT replay the backlog in latest.json.
# Mark everything currently in the window as seen and send nothing.
if last_guid == 0:
    newest = max((i.get("guid") or 0 for i in items), default=0)
    save_state(newest)
    print(f"No saved state: seeded last_guid={newest}, sent nothing.")
    raise SystemExit(0)

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

    # Stale headline (older than the real-time window): mark seen, don't send
    if age_minutes(item) > MAX_AGE_MIN:
        print(f"[skip stale] {headline}")
        highest_guid = max(highest_guid, guid)
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

    try:
        delivered = post({"embeds": [embed]})
    except Exception as e:
        print(e)
        delivered = False

    if not delivered:
        # Stop here so this and later items are retried on the next run
        # (the age guard keeps retries from ever becoming "old news").
        print(f"Discord delivery failed, will retry: {headline}")
        break

    print(f"sent: {headline}")
    highest_guid = max(highest_guid, guid)
    save_state(highest_guid)  # persist progress after every send

    time.sleep(1)

save_state(highest_guid)

print("Finished Discord notifications.")
