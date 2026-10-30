---
name: dev-save
description: Any time — save this session's progress into the project's CLAUDE.local.md before the user leaves — whether or not the current sub-spec is finished. Use when the user says they're wrapping up, stepping away, or closing the session, or asks to checkpoint, save progress, or update their local notes.
model: inherit
effort: low
---

Work as an engineer writing a handoff note to their future self: facts first, decisions with their reasons, and a resume point precise enough to start the next session without rereading the code.

## 1. Gather facts

- Read the project's `CLAUDE.local.md`. If it doesn't exist, ask whether to create one rather than assuming.
- Read `spec/INDEX.md` if it exists, to tie this session to its sub-spec.
- Collect the state: current branch, last commit (`git log -1 --oneline`), uncommitted files (`git status --short`), and the Verification and Review status in the sub-spec's `test-report.md`.
- Go back over this conversation for what was actually done, decided, verified, and left open. If nothing substantive happened, say so and write nothing.

## 2. Write the entry

Insert it above the existing log entries (newest first) and above the user's "Your notes" section. Never edit or reorder what's already there, and never touch the user's notes.

```markdown
**[YYYY-MM-DD] Sub-spec NN (<slug>) — checkpoint, <in-progress | verified | reviewed | blocked>**
- State: branch <name> · last commit <hash subject> · <n> uncommitted files · verification <status> · review <status>
- Done: <what changed, with file names>
- Decisions: <decision — reason; only real ones>
- Open: <unresolved items and blockers>
- Resume: <the exact next step — the command to run (`/dev-N-… NN`) or the function to finish>
```

If the session name matches the sub-spec slug (the user's one-session-per-sub-spec convention), mention it so the entry can be matched to its session.

## 3. Report

Show the entry you wrote and confirm nothing else in the file changed.
