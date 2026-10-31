---
name: dev-5-fix-review
description: Step 5 — work through the review findings for one sub-spec. Checks each finding against the code, lets the user decide fix, accept or reject per finding, applies the approved fixes with regression tests, and records every decision in the test report. Pass the sub-spec number, e.g. /dev-5-fix-review 04.
argument-hint: "<NN>"
disable-model-invocation: true
model: inherit
effort: high
allowed-tools: Bash(git status:*) Bash(git log:*) Bash(git diff:*) Bash(git branch --show-current) Bash(git rev-parse:*) Bash(python ${CLAUDE_PLUGIN_ROOT}/scripts/usage_ledger.py:*)
---

Work as the engineer answering a code review: take every finding seriously but verify it before acting, fix the cause rather than the symptom, never quietly relax the spec to make a finding go away, and leave a written answer for each finding.

Sub-spec: $ARGUMENTS (if empty, ask which one). Run everything from the repository root.

## 1. Load the findings

1. Read `spec/NN-*/test-report.md`. If `## Review` says "not yet run", stop and point to `/dev-4-review NN`. If both reviewers are clean, say so and end with `Next: /dev-6-final NN`.
2. Read `spec/NN-*/sub-spec.md`, `spec/NN-*/contract.md` and any earlier `## Review resolutions` rounds, so a finding already accepted isn't asked again unless the code around it changed.
3. The current branch must be `subspec/NN-<slug>`.

## 2. Check each finding against the code

Reviewers read a diff without running anything, so some findings are wrong. For each one, read the cited code and classify it:
- **confirmed** — the defect is real; note the root cause and the smallest correct fix.
- **already fixed** — the code no longer has it; cite the line.
- **not a defect** — the reviewer misread the code or the spec; cite the evidence. Code that follows a contract decision is not a defect for disagreeing with it; cite the decision (`D<n>`).
- **spec question** — the code matches one reading of something neither the spec nor the contract settles; this is a decision for the user, not a code change. Once decided, it goes into the contract's `## Late decisions`.

When a **confirmed** finding is a defect in an earlier, already-closed unit's code (or its contract), log it so review misses are counted: `python "${CLAUDE_PLUGIN_ROOT}/scripts/usage_ledger.py" escaped --unit <earlier unit> --found-in NN --kind defect --note "<one line>"`. Likewise when this unit's contract forces an edit to an earlier unit's locked files, log it with `--kind coupling`.

Where a finding claims a runtime behaviour (a shape, a leak, a NaN), prove or disprove it with a short script in the scratchpad rather than by reasoning alone.

## 3. Decide with the user

Show all findings in one table, most severe first: reviewer, severity, `file:line`, finding, your classification with evidence, proposed fix, and its blast radius (files touched, whether results computed earlier become invalid). Then ask through AskUserQuestion, per finding: **fix**, **accept** (a known limitation, with a reason), or **reject** (not a defect). Batch the questions; never decide for the user, and never fold a finding into a vaguer one.

## 4. Fix

For each finding marked fix:
- Fix the root cause in the implementation. Never weaken a spec requirement, a threshold, or a check to make a finding pass; if that's the only way, return it to the user as a spec question.
- Add or tighten an ordinary unit test that fails without the fix. Don't edit the independent verification file `test_subspec_NN_*.py` unless the finding is a defect in that file itself and the user agreed to it.
- Stay inside the finding: no unrelated refactors, and no new guards, config couplings or checks the finding didn't ask for (a fix that adds them tends to become the next round's finding).
- Code the user edited by hand is authoritative: fix around it, never revert it; if the finding is in their edit, ask before changing it.

Run the project's full test suite after all fixes, and report the counts.

## 5. Record

Append a round to `## Review resolutions` in `spec/NN-*/test-report.md` (create the section after `## Review` if it doesn't exist; never edit earlier rounds or the `## Review` section itself):

```markdown
## Review resolutions
### Round <n> — YYYY-MM-DD HH:MM · against review fingerprint <fingerprint from ## Review>
- [fixed] <reviewer> <file:line> — <finding> → <what changed, test added>
- [accepted] <reviewer> <file:line> — <finding> → <reason, and where the limitation is noted>
- [rejected] <reviewer> <file:line> — <finding> → <evidence>
```

When an accepted finding leaves work for a later unit ("09 must record the encoder hash", "16 must call the check before loading"), add a row to `spec/HANDOFFS.md` (`HO-<next number> | NN | <receiving unit> | <obligation> | open`) and end the resolution line with `→ HO-<n>`. That is how the obligation reaches the receiving unit's contract instead of being rediscovered by its reviewers.

## 6. Next step

Before the `Next` line, give a three-line checkpoint so the user always knows where the unit stands: **Done** (this stage, one line) · **Changed** (files touched, or none) · **Decided** (decisions made here, or nothing new).


Fixes change the code, so the recorded verification and review no longer match it, and `/dev-6-final` will refuse stale reports. End with one line:
- any finding fixed → `Next: /dev-3-test NN`, then `/dev-4-review NN`
- nothing fixed (all accepted or rejected) → `Next: /dev-6-final NN`
