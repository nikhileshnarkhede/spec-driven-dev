---
name: no-claude-footprint
description: Make sure a git repository shows no trace of Claude Code — gitignore its files, block commits that contain them or credit Claude in the message, and report traces already in history. Use at the start of work in a repo, before its first commit, or when asked to hide or check for the Claude Code footprint.
model: inherit
effort: low
---

Work as the repository's hygiene guard. The user's standing rule is that nothing pushed shows Claude Code was involved: no Claude Code files, and no commit message or PR text crediting Claude. Enforce what git hooks can enforce, since a hook catches what an instruction alone can miss.

Run in the repository root (`git rev-parse --show-toplevel`); if this isn't a git repository, say so and stop.

## 1. `.gitignore`

Make sure `.gitignore` contains these lines, adding only the missing ones and leaving the rest of the file untouched:

```
# Claude Code (no footprint)
CLAUDE.md
CLAUDE.local.md
.claude/
```

## 2. Hooks

Install both hooks under `.git/hooks/` and make them executable. Each block is wrapped in `# >>> no-claude-footprint` / `# <<< no-claude-footprint` markers so this step is safe to repeat: if a hook file contains the markers, replace the marked block with the current version; if it exists without them, append the block; if it doesn't exist, create it with `#!/bin/sh` followed by the block.

`pre-commit` — refuses to commit Claude Code files at any depth:

```sh
# >>> no-claude-footprint
blocked=$(git diff --cached --name-only | grep -E '(^|/)CLAUDE(\.local)?\.md$|(^|/)\.claude/' || true)
if [ -n "$blocked" ]; then
  echo "Blocked by no-claude-footprint: staged Claude Code files:" >&2
  echo "$blocked" >&2
  echo "Unstage them with: git restore --staged <file>" >&2
  exit 1
fi
# <<< no-claude-footprint
```

`commit-msg` — refuses messages that credit Claude:

```sh
# >>> no-claude-footprint
if grep -qiE 'co-authored-by:.*(claude|anthropic)|noreply@anthropic\.com|generated (with|by) .*claude' "$1"; then
  echo "Blocked by no-claude-footprint: the commit message credits Claude. Remove that line and commit again." >&2
  exit 1
fi
# <<< no-claude-footprint
```

Prove both hooks block what they should in a throwaway repository in a temp directory — one commit attempt each — then delete it. Never test by committing in the user's repository.

## 3. Existing traces

Report these without changing anything:
- Claude Code files already tracked: `git ls-files | grep -E '(^|/)CLAUDE(\.local)?\.md$|(^|/)\.claude/'`. A `.gitignore` entry doesn't untrack them; ask before `git rm --cached`.
- Commits whose message credits Claude: `git log --all -i -E --grep='co-authored-by:.*(claude|anthropic)|noreply@anthropic\.com|generated (with|by) .*claude' --format='%h %s'`. For each, check whether it's already pushed (`git branch -r --contains <hash>`), because that changes the risk of rewriting it. Rewriting history needs the user's explicit go-ahead.

## 4. Report

What changed in `.gitignore`, each hook's state (created, updated, appended, or already current), whether the proof passed, and any existing traces.
