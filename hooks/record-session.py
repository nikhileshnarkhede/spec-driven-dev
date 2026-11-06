"""Stop hook: register this session's transcript path for the usage ledger.

Why this exists. The usage ledger (scripts/usage_ledger.py) measures what a unit cost by reading
the session transcripts Claude Code writes. Claude Code tells hooks where the current transcript is
(`transcript_path` on stdin) but tells skills nothing, so this hook records the path once per session
and the ledger reads only transcripts registered here. The ledger therefore never searches the home
directory on its own, and the whole data path is in this file and the ledger script.

What it writes: one JSON line per session to ~/.claude/workflow-metrics/sessions.jsonl —
session_id, cwd, transcript_path and the time it was last seen. Nothing is read from the transcript,
nothing is sent anywhere, and a failure here never interrupts Claude Code.
"""
import json
import sys
import time
from pathlib import Path

REGISTRY = Path.home() / ".claude" / "workflow-metrics" / "sessions.jsonl"


def last_session_id(path):
    """session_id on the registry's last line, or None (reads only the tail of the file)."""
    try:
        with path.open("rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 4096))
            tail = f.read().decode("utf-8", errors="replace").strip().splitlines()
        return json.loads(tail[-1]).get("session_id") if tail else None
    except (OSError, ValueError, IndexError):
        return None


def main():
    event = json.load(sys.stdin)
    sid, transcript = event.get("session_id"), event.get("transcript_path")
    if not sid or not transcript:
        return
    if last_session_id(REGISTRY) == sid:
        return  # already registered by an earlier turn of this session
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    row = {"session_id": sid, "cwd": event.get("cwd"), "transcript_path": transcript,
           "seen": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())}
    with REGISTRY.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # a broken registry must never break Claude Code itself
