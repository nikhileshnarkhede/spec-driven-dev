"""PreToolUse hook for spec-verification-writer: keep the independent test writer away from the change.

/dev-3-test writes the change set's files to <git-dir>/verification-writer-denylist before launching the
writer, and removes the list afterwards. While the list exists, Read of a listed file, or Grep pointed at
one, is refused: a writer that has seen the implementation (or the implementer's own tests) tends to
encode what the code does instead of what the spec says. The writer's own test_subspec_NN_*.py file and
conftest.py stay readable.
Directory-wide Grep is not filtered; the writer's instructions cover that.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def norm(path: Path) -> str:
    return os.path.normcase(str(path.resolve()))


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0
    tool_input = event.get("tool_input") or {}
    target = tool_input.get("file_path") or tool_input.get("path") or ""
    if not target:
        return 0
    try:
        git_dir = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True, text=True,
                                 timeout=5).stdout.strip()
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                             timeout=5).stdout.strip()
    except Exception:
        return 0
    denylist = Path(git_dir) / "verification-writer-denylist" if git_dir else None
    if not denylist or not denylist.is_file() or not top:
        return 0
    own_file = re.compile(r"^test_subspec_\d+.*\.py$")
    denied = {norm(Path(top) / line.strip()) for line in denylist.read_text(encoding="utf-8").splitlines()
              if line.strip() and Path(line.strip()).name != "conftest.py"
              and not own_file.match(Path(line.strip()).name)}
    candidate = Path(target) if os.path.isabs(target) else Path(top) / target
    if norm(candidate) in denied:
        print(f"Blocked: {Path(target).name} is part of the change under test. The independent test writer "
              "works from the sub-spec, the contract and the interface surface only; write the check "
              "against the contract's interface instead.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
