#!/usr/bin/env python3
"""
Continuous FinancialJuice poller (replaces slow cron-per-run polling).

Calls collect.main() every LIVE_INTERVAL seconds for LIVE_DURATION_SEC
seconds. collect.main() fetches the feed, appends new headlines, rewrites
latest.json and (when there is something new) runs discord.py -- so news
reaches Discord within ~one interval of FinancialJuice publishing it.

Env:
  LIVE_INTERVAL      seconds between polls            (default 10)
  LIVE_DURATION_SEC  total runtime, then exit cleanly (default 20400 = 340 min)
  LIVE_COMMIT        "1" -> git commit+push state/archive/latest as they change
                     (GitHub Actions). Leave unset on your own server.
  DISCORD_WEBHOOK    Discord webhook URL

Run anywhere always-on:   DISCORD_WEBHOOK=... python live.py
"""

import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

import collect

HERE = Path(__file__).parent
INTERVAL = float(os.environ.get("LIVE_INTERVAL", "10"))
DURATION = float(os.environ.get("LIVE_DURATION_SEC", str(340 * 60)))
COMMIT = os.environ.get("LIVE_COMMIT") == "1"
HEARTBEAT = 600  # push latest.json at least this often (seconds)

FILES = ["archive.jsonl", "latest.json", "state.json"]


def git(*args):
    return subprocess.run(["git", *args], cwd=HERE, capture_output=True, text=True)


def push(msg):
    """Commit tracked data files and push, rebasing over other workflows."""
    git("add", *FILES)
    if git("diff", "--cached", "--quiet").returncode == 0:
        return
    git("commit", "-m", msg)
    for _ in range(4):
        git("pull", "--rebase", "--autostash")
        if git("push").returncode == 0:
            return
        time.sleep(2)
    print("WARNING: git push failed after retries", flush=True)


def fingerprint():
    """Changes only when new headlines arrived or Discord state moved."""
    out = []
    for name in ("archive.jsonl", "state.json"):
        p = HERE / name
        out.append(p.stat().st_size if p.exists() else 0)
    return tuple(out)


def main() -> int:
    if COMMIT:
        git("config", "user.name", "fj-collector")
        git("config", "user.email", "actions@users.noreply.github.com")
        git("pull", "--rebase", "--autostash")

    end = time.monotonic() + DURATION
    last = fingerprint()
    last_push = time.monotonic()
    errors = 0

    print(f"live: polling every {INTERVAL:.0f}s for {DURATION/60:.0f} min", flush=True)

    while time.monotonic() < end:
        started = time.monotonic()
        try:
            collect.main()
            errors = 0
        except Exception:
            errors += 1
            print(f"poll failed ({errors}):", flush=True)
            traceback.print_exc()

        if COMMIT:
            now = time.monotonic()
            cur = fingerprint()
            if cur != last:
                push("live: new headlines")
                last, last_push = fingerprint(), now
            elif now - last_push > HEARTBEAT:
                push("live: heartbeat")
                last_push = now

        # back off a little if the feed keeps failing
        wait = INTERVAL * (1 + min(errors, 6))
        time.sleep(max(1.0, wait - (time.monotonic() - started)))

    if COMMIT:
        push("live: final")
    print("live: done", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
