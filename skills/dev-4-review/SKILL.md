---
name: dev-4-review
description: Step 4 — independent parallel review of the current sub-spec's change — spec and contract compliance plus ML/data-pipeline risk — recorded against the exact code state reviewed. After fixes, a focused re-review checks the fixed findings and what changed since the last review. Pass the sub-spec number, e.g. /dev-4-review 04.
argument-hint: "<NN>"
disable-model-invocation: true
model: inherit
effort: low
allowed-tools: Bash(git status *) Bash(git log *) Bash(git diff *) Bash(git branch *) Bash(git rev-parse *) Bash(python *)
---

Work as a review coordinator: give two independent reviewers the change and the documents it must satisfy, keep their findings separate, and record them against the exact code state reviewed.

Sub-spec: $ARGUMENTS (if empty, ask which one). Run everything from the repository root. `CS` below stands for `python "${CLAUDE_SKILL_DIR}/../dev-3-test/scripts/changeset.py"`.

## 1. Full review or focused re-review

A **focused re-review** applies when all of these hold:
- `.git/subspec-NN-review.tree` exists (a previous review recorded the state it saw);
- `## Review resolutions` has a round against the fingerprint in the current `## Review`, so every earlier finding has an answer;
- the change since then is small: run `CS --since subspec-NN-review.tree` and check it touches less than 40% of the full change's changed lines;
- it doesn't change a signature listed in the contract's `## Interfaces` (run `interface_surface.py` from `dev-3-test/scripts` on the changed files and compare).

Otherwise, or if the user asks for it, do a **full review**. A large or interface-changing fix can break code the delta doesn't show, so it gets the full look again.

## 2. Capture the change

- Full review: `CS --write subspec-NN-review.diff --snapshot subspec-NN-review.tree`
- Focused re-review: `CS --since subspec-NN-review.tree --write subspec-NN-delta.diff --snapshot subspec-NN-review.tree`

Either way, the command prints the fingerprint of the full change (it goes in the record), writes the diff the reviewers read, and records the reviewed state for the next re-review. The reviewers have no shell, which keeps them strictly read-only; they read the diff file and open surrounding code with Read.

## 3. Review in parallel

Inputs for both reviewers: the sub-spec path, `spec/NN-*/contract.md`, `spec/CONVENTIONS.md`, and the diff file path.

**Full review.** In one message, launch both:
- `spec-compliance-reviewer`, with the inputs plus the `## Verification` section of `test-report.md` — its list of statements without a check deserves the closest reading.
- `pipeline-risk-reviewer`, with the inputs.

Both briefs state the budget. Compliance: a table with one row per acceptance check and incoming handoff (verdict and evidence), then at most 10 findings. Pipeline: the contract's risks and the hazard register first, at most 8 findings, and no finding for a limitation already recorded in the contract, `spec/HANDOFFS.md` or the resolutions. (Across 19 SCANIA units the two reviews were 36% of all tokens and most findings were already-known limitations.)

**Focused re-review.** In one message, launch both:
- `spec-compliance-reviewer`, in re-review mode;
- `pipeline-risk-reviewer-recheck` (the same reviewer, scoped to the delta).

Give each the inputs plus the previous `## Review` and the latest `## Review resolutions` round, and this scope: confirm each finding marked fixed is really fixed; review the changed code, including how it interacts with the code it calls and is called by; don't re-raise findings already accepted or rejected unless the change affects them.

## 4. Record

Show both reports to the user, separated by reviewer, most severe first. Don't merge, deduplicate or soften them, and don't fix anything — fixing is `/dev-5-fix-review`, with the user deciding each finding. Replace only the `## Review` section of `spec/NN-*/test-report.md`, leaving `## Review resolutions` untouched:

```markdown
## Review
_Last run: YYYY-MM-DD HH:MM · change-set fingerprint: <fingerprint> · <full review | focused re-review: N files changed since <previous fingerprint>>_

### spec-compliance-reviewer
- [<severity>] <file:line> — <finding>   (or: clean)

### pipeline-risk-reviewer
- [<severity>] <file:line> — <finding>   (or: clean)
```

Record every finding, resolved or not — the report is the record, not just a gate.
Before the `Next` line, give a three-line checkpoint so the user always knows where the unit stands: **Done** (this stage, one line) · **Changed** (files touched, or none) · **Decided** (decisions made here, or nothing new). End with one line:
- both reviewers clean → `Next: /dev-6-final NN`
- any finding → `Next: /dev-5-fix-review NN` (the user decides, finding by finding, what to fix and what to consciously accept)
