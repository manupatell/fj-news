import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from filters import get_tag, is_high_impact

HERE = Path(__file__).parent
LATEST = HERE / "latest.json"
STATE = HERE / "state.json"

WEBHOOK = os.environ.get("DISCORD_WEBHOOK")

# Real-time guard: never post a headline published more than this many
# minutes ago, even if its GUID is "unseen" (lost state, failed push, etc.)
MAX_AGE_MIN = int(os.environ.get("DISCORD_MAX_AGE_MIN", "60"))

if not WEBHOOK:
    print("ERROR: DISCORD_WEBHOOK environment variable is missing.")
    raise SystemExit(1)


SEEN_MAX = 2000


def load_state():
    """State = {"last_guid": int, "seen": [guid, ...]}.

    FinancialJuice GUIDs are NOT strictly increasing with publish time
    (data-release bursts arrive out of order), so we track the set of
    GUIDs already handled instead of a single high-water mark.
    """
    if not STATE.exists():
        return {"last_guid": 0, "seen": []}

    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
        state["last_guid"] = int(state.get("last_guid") or 0)
        state["seen"] = [int(g) for g in state.get("seen", [])]
        return state
    except Exception:
        return {"last_guid": 0, "seen": []}


def save_state(last_guid, seen):
    seen = sorted(set(seen))[-SEEN_MAX:]
    STATE.write_text(
        json.dumps({"last_guid": last_guid, "seen": seen}),
        encoding="utf-8",
    )


def _data_title(headline: str):
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


TAG_TITLES = {
    "GOLD": "🥇 GOLD / XAUUSD",
    "NASDAQ": "📈 NASDAQ / MNQ",
    "GEOPOLITICS": "🌍 GEOPOLITICS",
    "FED": "🏦 FED",
    "FED SPEAKER": "🏦 FED SPEAKER",
    "YIELDS": "💵 YIELDS / USD",
    "US POLICY": "🇺🇸 US POLICY",
    "TRUMP": "🇺🇸 TRUMP",
}


def get_title(headline: str):
    tag = get_tag(headline)
    if tag in TAG_TITLES:
        return TAG_TITLES[tag]
    return _data_title(headline)


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
# oldest -> newest by publish time (GUID order is unreliable)
items = sorted(data["items"], key=lambda i: (i.get("ts") or "", i.get("guid") or 0))

state = load_state()
last_guid = state["last_guid"]
seen = set(state["seen"])

# First run / lost state: do NOT replay the backlog in latest.json.
if last_guid == 0 and not seen:
    seen = {i["guid"] for i in items if i.get("guid")}
    last_guid = max(seen, default=0)
    save_state(last_guid, seen)
    print(f"No saved state: seeded {len(seen)} guids, sent nothing.")
    raise SystemExit(0)

# Migration from the old format (only last_guid): everything at or below it
# was already handled.
if not seen:
    seen = {i["guid"] for i in items if i.get("guid") and i["guid"] <= last_guid}

for item in items:

    guid = item.get("guid") or 0

    if not guid or guid in seen:
        continue

    headline = item["headline"]

    ok, color = is_high_impact(headline)

    if not ok:
        seen.add(guid)
        continue

    # Stale headline (older than the real-time window): mark seen, don't send
    if age_minutes(item) > MAX_AGE_MIN:
        print(f"[skip stale] {headline}")
        seen.add(guid)
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
        # Leave it unseen so the next run retries (age guard bounds retries)
        print(f"Discord delivery failed, will retry: {headline}")
        break

    print(f"sent: {headline}")
    seen.add(guid)
    last_guid = max(last_guid, guid)
    save_state(last_guid, seen)  # persist after every send

    time.sleep(1)

last_guid = max([last_guid] + [g for g in seen if g])
save_state(last_guid, seen)

print("Finished Discord notifications.")
