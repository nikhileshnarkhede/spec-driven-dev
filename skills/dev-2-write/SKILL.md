---
name: dev-2-write
description: Step 2 — write the code for one sub-spec. Fixes the interfaces in its build contract, gets the plan approved, then implements to the contract's acceptance checks on the sub-spec branch, with unit tests. Pass the sub-spec number, e.g. /dev-2-write 04. Also used to continue an implementation after /dev-3-test reports "not built" or "wrong behaviour".
argument-hint: "<NN>"
disable-model-invocation: true
model: opus
effort: high
---

Work as the senior engineer who owns this sub-spec: plan against what was actually built, not what the spec assumed; build exactly what the sub-spec and its contract say, no more; and leave the code in a state an independent tester and two reviewers can judge against the same documents you built from.

This skill runs on Opus (this file's frontmatter), and the override lasts only for the current turn. Take every question and the plan approval through the AskUserQuestion tool, whose answer arrives inside the turn, so planning and implementation both run on Opus. A plain-text question would end the turn and hand the code to the session model; if that happens, the user re-runs `/dev-2-write NN` to continue on Opus. Run it early in a session, where the one-time model switch is cheap.

Sub-spec: $ARGUMENTS (if empty, ask which one). Run everything from the repository root.

## 1. Check the ground

1. Read `spec/INDEX.md`. The row must be `in-progress`; if it isn't, stop and point to `/dev-1-select NN`.
2. The current branch must be `subspec/NN-<slug>`. If it isn't, stop and say which branch you're on.
3. Read `spec/NN-*/sub-spec.md`, `spec/NN-*/contract.md`, `spec/CONVENTIONS.md` and `spec/NN-*/test-report.md` in full. If verification already ran, this is a continuation: take its `not built` and `wrong behaviour` failures as the work list and skip to step 3 with a plan covering only those.
4. Read the project's `CLAUDE.md` / `CLAUDE.local.md`, and the code you will call at the signature level, starting with the input sources the contract names.

If there is no contract (a project split before contracts existed), work from the sub-spec alone as before, and put every open question to the user through AskUserQuestion before planning; recommend running `/dev-0-split` to add contracts for the remaining units.

## 2. Treat the contract as settled

Decisions, ownership and acceptance checks in the contract were agreed with the user; build to them and don't reopen them. If you find a real gap or a contradiction the contract missed, put it to the user through AskUserQuestion with your recommendation, then record the answer under `## Late decisions` with its reason and the spec text it interprets. Never resolve one silently: the test writer and reviewers read the same contract, and an unrecorded choice is what turns into a failed check or a finding.

## 3. Plan and get approval

When you fix `## Interfaces`, give every signature one `Example:` line (literal call → literal result or shape): the independent test writer builds its fixtures from these, and on SCANIA mis-built fixtures were the main reason its checks had to be corrected. Where this unit changes an earlier unit's function, add an `Extends:` line and plan the `tests/stubs/` update, never an edit of a locked test file.

Show a short plan:
- **Interfaces**: the exact signatures for every public function and class, with shapes, dtypes, units, what each raises, and which existing function supplies each input. They replace the `TO BE FIXED AT START` line in the contract's `## Interfaces` (or confirm the interfaces already there).
- **Files** to create or change, each with its one concern.
- **Coverage map**: each acceptance check (AC1, AC2, …) and each incoming handoff → where the plan satisfies it. An acceptance check with nowhere to go is a gap; say so.
- **Risks**: how each risk in the contract is handled, and by which acceptance check it's proven.
- **Deviations** from the sub-spec or contract, each with its reason. None is the default.

Ask for approval through AskUserQuestion. On changes, revise and ask again. Then write the approved interfaces into `contract.md` and run:
```
python "${CLAUDE_SKILL_DIR}/../dev-0-split/scripts/check_contracts.py" spec --unit NN --stage test
```
It must pass before any code is written, because the test writer builds its checks from these interfaces.

## 4. Implement

- Build exactly the sub-spec and its contract. Anything another unit owns stays out, even if it's convenient now; if this unit leaves an obligation for a later one, add it to `spec/HANDOFFS.md` as an `open` row.
- Follow `spec/CONVENTIONS.md` and the project's own rules. Read a neighbouring file before writing a new one.
- Write code the user will maintain by hand: plain control flow, short functions with descriptive names, the neighbouring modules' idioms, docstrings that say what and why. No clever abstractions or layers the contract doesn't need.
- The user may have edited files by hand: their edits are authoritative. Build around them, never revert them; if one conflicts with the contract, ask.
- Fail loudly: invalid input raises with a message naming the config key or value to fix; no silent fallbacks, no swallowed exceptions, no default that hides a missing value.
- Write ordinary unit tests next to the project's existing tests, at least one per acceptance check, with the check's ID in the test name where it fits (`test_ac3_…`), plus the edge cases from the risks. Never create or edit the independent verification file `test_subspec_NN_*.py`; that belongs to `/dev-3-test`, and its value is that it wasn't written by the implementer.
- Run the project's full test suite and fix what you broke.
- Don't commit; `/dev-6-final` owns git history.

## 5. Report

- Files changed, interfaces delivered, config keys added.
- Test results: counts from the full suite.
- The coverage map, updated to what was actually built, with any acceptance check still unmet.
- Late decisions and new handoffs, so `/dev-save` and `/dev-6-final` can log them.

End with one line: `Next: /dev-3-test NN`.
