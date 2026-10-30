import json
import os
import subprocess
import time

STALE_MINUTES = 20


def main():
    p = os.path.join(os.getcwd(), "CLAUDE.local.md")
    if not os.path.isfile(p):
        return  # this project doesn't use the CLAUDE.local.md convention

    age_min = (time.time() - os.path.getmtime(p)) / 60
    if age_min <= STALE_MINUTES:
        return  # recently checkpointed (or just created) -- nothing to nag about

    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=5,
        )
        dirty = result.stdout.strip()
    except Exception:
        dirty = ""

    if not dirty:
        return  # no uncommitted work -- nothing to lose, no reminder needed

    msg = (
        f"CLAUDE.local.md hasn't been updated in {int(age_min)} min and this repo "
        "has uncommitted changes -- run /dev-save before you wrap up."
    )
    print(json.dumps({"systemMessage": msg}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # a broken reminder must never break Claude Code itself
