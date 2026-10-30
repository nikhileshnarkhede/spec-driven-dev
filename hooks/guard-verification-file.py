"""PreToolUse hook for implementer agents: block edits to the independent verification file.

The verification file (test_subspec_NN_*.py) is written by spec-verification-writer from the
spec alone. If the agent that writes the code could also edit those checks, a failing check
could be "fixed" by weakening it, so the hook refuses Write/Edit on that file name.

Registered in hooks/hooks.json with --require-agent: a plugin hook fires in the main session and
in every agent, so with that flag the hook acts only when the hook input's agent_type names an
implementer agent (dev-implementer, dev-implementer-max, with or without a plugin prefix) and
lets every other call through. Without the flag it blocks unconditionally, for a hook attached
to one agent directly.
"""
import json
import os
import re
import sys

PATTERN = re.compile(r"^test_subspec_\d+.*\.py$")
GUARDED_AGENTS = {"dev-implementer", "dev-implementer-max"}


def guarded_agent(event: dict, require_agent: bool) -> bool:
    """True when the hook should act on this call."""
    if not require_agent:
        return True
    agent = str(event.get("agent_type") or "")
    return agent.split(":")[-1] in GUARDED_AGENTS


def main():
    require_agent = "--require-agent" in sys.argv[1:]
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0  # unreadable input: never break the tool call
    if not guarded_agent(event, require_agent):
        return 0
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
