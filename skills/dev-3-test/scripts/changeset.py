"""Summarise the current branch's change since it left the base branch, with a fingerprint.

  changeset.py [--base BRANCH] [--write NAME]       full change since the base branch (+ fingerprint)
  changeset.py --snapshot NAME                       also record the current state, to diff against later
  changeset.py --since NAME [--write NAME2]          also show only what changed since that snapshot

Snapshots are git tree objects built in a temporary index: no commit, branch, stash or index change.
spec/ is excluded everywhere, so report edits never count as code changes.
"""
import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

EXCLUDE = ":(exclude)spec"


def git(*args: str, ok_codes: tuple[int, ...] = (0,), env: dict | None = None) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8",
                            errors="replace", env=env)
    if result.returncode not in ok_codes:
        sys.exit(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def base_branch(requested: str | None) -> str:
    if requested:
        return requested
    for name in ("main", "master"):
        if subprocess.run(["git", "rev-parse", "--verify", "--quiet", name], capture_output=True).returncode == 0:
            return name
    sys.exit("no main or master branch found; pass --base")


def snapshot_tree(git_dir: Path) -> str:
    """Tree object of the working tree as it is now (tracked + untracked, .gitignore respected)."""
    index = git_dir / "changeset-snapshot.index"
    env = {**os.environ, "GIT_INDEX_FILE": str(index)}
    try:
        git("read-tree", "HEAD", env=env)
        git("add", "-A", "--", ".", EXCLUDE, env=env)
        return git("write-tree", env=env).strip()
    finally:
        index.unlink(missing_ok=True)


def changed_lines(numstat: str) -> int:
    total = 0
    for line in numstat.splitlines():
        added, deleted, *_ = line.split("\t")
        total += (int(added) if added.isdigit() else 0) + (int(deleted) if deleted.isdigit() else 0)
    return total


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", help="base branch (default: main, else master)")
    parser.add_argument("--write", metavar="NAME", help="save the diff as <git-dir>/NAME (the delta when --since is given)")
    parser.add_argument("--snapshot", metavar="NAME", help="record the current state as <git-dir>/NAME")
    parser.add_argument("--since", metavar="NAME", help="diff against the state recorded in <git-dir>/NAME")
    args = parser.parse_args()

    os.chdir(git("rev-parse", "--show-toplevel").strip())
    git_dir = Path(git("rev-parse", "--git-dir").strip()).resolve()
    base = base_branch(args.base)
    merge_base = git("merge-base", base, "HEAD").strip()
    tracked = [p for p in git("diff", "--name-only", "-z", merge_base, "--", ".", EXCLUDE).split("\0") if p]
    untracked = [p for p in git("ls-files", "--others", "--exclude-standard", "-z", "--", ".", EXCLUDE).split("\0") if p]

    diff = git("diff", merge_base, "--", ".", EXCLUDE)
    for path in untracked:
        diff += git("diff", "--no-index", "--", "/dev/null", path, ok_codes=(0, 1))
    fingerprint = hashlib.sha256(diff.encode("utf-8")).hexdigest()[:12]

    print(f"base: {base} (merge-base {merge_base[:12]})")
    print(f"fingerprint: {fingerprint}")
    print("changed tracked files:", *(tracked or ["(none)"]), sep="\n  ")
    print("new untracked files:", *(untracked or ["(none)"]), sep="\n  ")

    output = diff
    if args.snapshot or args.since:
        then = None
        if args.since:  # read before --snapshot can overwrite the same file
            recorded = git_dir / args.since
            if not recorded.is_file():
                sys.exit(f"no snapshot named {args.since}; run with --snapshot {args.since} first")
            then = recorded.read_text(encoding="utf-8").strip()
        now = snapshot_tree(git_dir)
        if args.snapshot:
            (git_dir / args.snapshot).write_text(now + "\n", encoding="utf-8")
            print(f"snapshot: {now[:12]} recorded as {git_dir / args.snapshot}")
        if then is not None:
            output = git("diff", then, now, "--", ".", EXCLUDE)
            delta_files = [p for p in git("diff", "--name-only", then, now, "--", ".", EXCLUDE).splitlines() if p]
            delta = changed_lines(git("diff", "--numstat", then, now, "--", ".", EXCLUDE))
            full = changed_lines(git("diff", "--numstat", merge_base, now, "--", ".", EXCLUDE))
            share = 100.0 * delta / full if full else 0.0
            print(f"since {args.since}: {len(delta_files)} files, {delta} changed lines "
                  f"({share:.0f}% of the {full} changed lines in the full change)")
            print("changed since the snapshot:", *(delta_files or ["(none)"]), sep="\n  ")

    if args.write:
        out = (git_dir / args.write).resolve()
        out.write_text(output, encoding="utf-8")
        print(f"diff written: {out}")


if __name__ == "__main__":
    main()
