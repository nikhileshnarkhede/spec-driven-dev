"""PreToolUse hook for implementer agents: block edits to the independent verification file.

The verification file (test_subspec_NN_*.py) is written by spec-verification-writer from the
spec alone. If the agent that writes the code could also edit those checks, a failing check
could be "fixed" by weakening it, so the hook refuses Write/Edit on that file name.
"""
import json
import os
import re
import sys

PATTERN = re.compile(r"^test_subspec_\d+.*\.py$")


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0  # unreadable input: never break the tool call
    path = (event.get("tool_input") or {}).get("file_path") or ""
    if PATTERN.match(os.path.basename(path)):
        print(
            f"Blocked: {os.path.basename(path)} is the independent verification file. "
            "Implementers may not edit it; fix the code, or report the check as a "
            "suspected test defect.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
