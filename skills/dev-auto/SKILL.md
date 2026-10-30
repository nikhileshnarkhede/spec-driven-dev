---
name: dev-auto
description: Unattended loop for one sub-spec — select, implement, test, review and fix in up to 3 rounds without asking the user, building to the unit's build contract (robustness checks included, so hardening is not a separate round). Records every decision in the test report and stops before /dev-6-final, which stays with the user. Pass the sub-spec number, e.g. /dev-auto 04.
argument-hint: "<NN> [--no-contract] [--here]"
disable-model-invocation: true
model: sonnet
effort: medium
allowed-tools: Read Grep Glob Write(./spec/**) Edit(./spec/**) Write(./.git/verification-writer-denylist) Bash(git status *) Bash(git log *) Bash(git diff *) Bash(git branch *) Bash(git rev-parse *) Bash(git switch *) Bash(git checkout -b *) Bash(git add spec/INDEX.md) Bash(git commit -m *) Bash(python "${CLAUDE_SKILL_DIR}/../dev-0-split/scripts/check_contracts.py" *) Bash(python "${CLAUDE_SKILL_DIR}/../dev-3-test/scripts/changeset.py" *) Bash(python "${CLAUDE_SKILL_DIR}/../dev-3-test/scripts/interface_surface.py" *) Bash(python "${CLAUDE_SKILL_DIR}/../../scripts/usage_ledger.py" *) Bash(python -m pytest *) Bash(pytest *)
---

Work as the engineering lead running an unattended build: delegate the work, keep the evidence honest, decide the way the user would decide, and write every decision down so the user can audit the run in two minutes afterwards. The user asked not to be interrupted, so ask nothing during the rounds; the only question comes at the end (hardening candidates, step 3). When a decision would normally be theirs, apply the rules below and record what you chose and why.

The unit's build contract (`spec/NN-*/contract.md`) is what makes one-round runs possible: the implementer, the test writer and both reviewers read the same settled decisions, interfaces, acceptance checks and robustness checks, so they don't each guess differently.

This coordinator runs on Sonnet and is itself the second-largest cost of a unit (17% across 19 SCANIA units, `~/.claude/workflow-metrics/LEDGER.md`), because every call re-reads the whole conversation. Keep it lean: the procedures are inlined below, so don't open the sister skills; pass agents file paths, not file contents, except the interface surface; summarise each agent report into the run log in at most ten lines (its full text goes once into the test report's own section); never re-read a file you wrote in this run.

Arguments: $ARGUMENTS — the sub-spec number (required; if missing, stop and say `/dev-auto NN`), optionally `--no-contract` and `--here`. Run everything from the repository root. Abbreviations: `CC` = `python "${CLAUDE_SKILL_DIR}/../dev-0-split/scripts/check_contracts.py" spec --unit NN`; `CS` = `python "${CLAUDE_SKILL_DIR}/../dev-3-test/scripts/changeset.py"`; `IS` = `python "${CLAUDE_SKILL_DIR}/../dev-3-test/scripts/interface_surface.py"`; `LEDGER` = `python "${CLAUDE_SKILL_DIR}/../../scripts/usage_ledger.py"`.

## 0. Unattended preconditions

Stop immediately, before changing anything, if:
- this conversation already holds other work (another unit, framework or analysis work, long discussion) and `--here` wasn't given → tell the user to start a fresh session (`/clear`) and run `/dev-auto NN` there. On 06 a carried-over context made the coordinator 66% of the unit's cost;
- `spec/INDEX.md` is missing, the row is `done`/`pre-existing`, or a dependency isn't `done`/`pre-existing`;
- the working tree has uncommitted changes outside `spec/` (unattended runs never carry stray work onto a branch); `spec/` itself untracked means the baseline commit never happened, which is the user's;
- `CC --stage start` fails:
  - no contract → recommend `/dev-0-split` (its upgrade mode writes the contracts and settles the decisions with the user). With `--no-contract`, continue the old way instead: resolve each header question by the reading most faithful to the spec text and log it as an assumption.
  - an open decision or an undecided header question → those are the user's: say which, and point to `/dev-1-select NN` to settle them, then `/dev-auto NN` again.
- a permission prompt is denied during the run (the user is away; stop instead of retrying).

Tell the user this run works best in auto mode, because any permission prompt stalls an unattended run. If the session isn't in auto mode, say so in one line and continue.

## 1. Select

Read `spec/INDEX.md`, the sub-spec and the contract. A row already `in-progress` on its own branch is resumed there; otherwise, from the main branch, `git checkout -b subspec/NN-<slug>`, set the row to `in-progress` and commit that change alone as `start NN: <title>` (no attribution line).

Bring the contract up to date, without asking:
- **Incoming handoffs.** Every `open` row in `spec/HANDOFFS.md` addressed to this unit is listed under `## Incoming handoffs`, mapped to the acceptance check that discharges it; add a check where none covers it.
- **Inputs.** For each existing function the Interfaces name as an input source, confirm the signature with `IS <files>`. Where the built code differs, correct the contract and log it: `LEDGER escaped --unit <earlier unit> --found-in NN --kind spec-gap --note "<what differed>"`.
- **Accepted limitations.** Read the dependencies' entries in `CLAUDE.local.md` and their `## Review resolutions`; one that affects this unit becomes a risk or a decision. If it would change behaviour, stop: that decision is the user's.
- **Locked tests touched.** The contract's `Extends:` lines name the earlier functions this unit changes; also grep the dependencies' `test_subspec_*` files for them. Where those checks go through `tests/stubs/`, the stub update is planned work for round 1. Where a locked file's own assertion would break and no recorded decision allows the edit, stop: editing a locked file is the user's call.

Re-run `CC --stage start` until it passes; the contract edits stay uncommitted (they belong to the unit's change). Create the run log: append `## Autonomous run` to `spec/NN-*/test-report.md` with the start time and what you changed in the contract.

## 2. Rounds (at most 3, plus at most one hardening round from step 3)

| Round | Implementer | Review |
|---|---|---|
| 1 | `dev-implementer` (Sonnet, high), mode `build` | full |
| 2 | `dev-implementer` (Sonnet, high), mode `fix` | focused re-review |
| 3 | `dev-implementer` again, or `dev-implementer-max` (Opus, xhigh) only when the work list holds failing checks, wrong behaviour or confirmed defects that round 2 could not close — never for minor items | focused re-review |

Any implementer launch carries at most 5 work items, most severe first; the rest wait for a follow-up launch on `dev-implementer`. (On SCANIA one Opus launch with an unbounded list cost 5.6M, a third of its unit.)

**a. Implement.** Launch the round's implementer with: the sub-spec path, the contract path, `spec/CONVENTIONS.md`, the round number and mode, the work list (empty in round 1; otherwise each item as `file:line`, class and observed value), and the run-log location. In round 3, add a short account of what rounds 1–2 tried and why it didn't close the list. In round 1 the implementer first fixes `## Interfaces` (exact signatures and one `Example:` line each); when it returns, `CC --stage test` must pass — if not, send the errors back once, then stop.

**b. Test.** Round 1 only: run `CS` for the change set; work out the test directory, framework and the exact command that runs one file; the verification file is `<test dir>/test_subspec_NN_<slug_with_underscores>.py`; run `IS` on the change set's non-test Python files. Write the change set's paths, one per line, to `<git-dir>/verification-writer-denylist`, then launch `spec-verification-writer` with: the sub-spec path, the contract path, `spec/CONVENTIONS.md`, the interface surface pasted in full, the framework and import conventions, a conftest or fixture file to reuse, the project's `tests/stubs/` module if it exists, and the exact file path to write. Never name the implementation files or describe how the code works. Delete the denylist as soon as the writer returns (and recreate it around every later writer launch).

Every round: launch `spec-verification-runner` with the verification file path, the command that runs it, the full-suite command and the contract path. Re-run `CS` for the fingerprint and replace only `## Verification`:

```markdown
## Verification
_Last run: YYYY-MM-DD HH:MM · change-set fingerprint: <fingerprint> · file: <verification file path>_

<N passed / M failed / K errors> · regressions elsewhere: <none, or list>

- [PASS] AC<n> <check> — <source>
- [FAIL · <not built | wrong behaviour | test defect | spec contradiction | environment>] AC<n> <check> — observed: <value>

Acceptance checks without a test, and spec statements without a check:
- AC<n> / §x: "<statement>" — <reason>
```

After the **first** run only, write one line in the run log, `First run by class: not built=<n>, wrong behaviour=<n>, test defect=<n>, spec contradiction=<n>, environment=<n>`; `/dev-6-final` records it in the ledger. Then:
- `not built` or `wrong behaviour` (code that doesn't match the contract's interfaces counts here) → next round's work list.
- `test defect` → read the check, the contract and the spec. If the check contradicts them, relaunch the writer once to correct exactly those checks, citing the acceptance check or spec statement, and log it. Never loosen a check because the code fails it. A failure in an earlier unit's locked `test_subspec_*` file caused by this unit's contract: if a recorded decision allows stub or fixture updates for that file, relaunch the writer on it under that decision; otherwise stop.
- `spec contradiction` → log it and stop (it needs the user).
- `environment` → stop and report what's missing.

**c. Review, only when verification fully passes.** Reviewing failing code wastes tokens on findings the next round will move. A **focused re-review** applies when `.git/subspec-NN-review.tree` exists, every earlier finding has a resolution, `CS --since subspec-NN-review.tree` touches less than 40% of the change's changed lines, and no signature in `## Interfaces` changed (`IS` on the changed files); otherwise do a **full review**. Capture the change — full: `CS --write subspec-NN-review.diff --snapshot subspec-NN-review.tree`; focused: `CS --since subspec-NN-review.tree --write subspec-NN-delta.diff --snapshot subspec-NN-review.tree` — then launch both reviewers in one message with the sub-spec path, the contract path, `spec/CONVENTIONS.md` and the diff path:
- full → `spec-compliance-reviewer` (plus the `## Verification` section) and `pipeline-risk-reviewer`;
- focused → `spec-compliance-reviewer` in re-review mode and `pipeline-risk-reviewer-recheck`, each with the previous `## Review` and the latest resolutions round, scoped to: confirm fixed findings are fixed, review the changed code with its callers and callees, don't re-raise accepted or rejected findings unless the change affects them.

Both briefs state the budget. Compliance: a table with one row per acceptance check and incoming handoff (verdict and evidence), then at most 10 findings. Pipeline: the contract's risks and the hazard register first, at most 8 findings, and no finding for a limitation already recorded in the contract, `spec/HANDOFFS.md` or the resolutions. Replace only `## Review`:

```markdown
## Review
_Last run: YYYY-MM-DD HH:MM · change-set fingerprint: <fingerprint> · <full review | focused re-review: N files changed since <previous fingerprint>>_

### spec-compliance-reviewer
- [<severity>] <file:line> — <finding>   (or: clean)

### pipeline-risk-reviewer
- [<severity>] <file:line> — <finding>   (or: clean)
```

**d. Decide findings without the user.** Classify each finding against the cited code: **confirmed** (root cause and smallest fix), **already fixed** (cite the line), **not a defect** (reviewer misread the code or the spec; code that follows a contract decision is not a defect, cite `D<n>`), or **spec question** (neither spec nor contract settles it). Prove or disprove any claimed runtime behaviour with a short script in the scratchpad. Then apply these rules:
- A confirmed defect in an earlier, closed unit, or a locked file edited because of this unit's contract → also `LEDGER escaped --unit <earlier unit> --found-in NN --kind defect|coupling --note "<one line>"`.
- **confirmed**, critical/high/medium, or blocker/major/results-invalidating → fix: next round's work list.
- **confirmed**, low/minor → fix if local to one function and no interface changes; otherwise accept, with the reason.
- **confirmed**, `fragile`: if a robustness acceptance check or a contract risk already covers the behaviour, it is wrong behaviour → fix. Otherwise it is a hardening candidate: add it to `### Hardening candidates` in the run log with a one-line cost/benefit and the hazard it would belong to, and don't fix it during the rounds.
- **not a defect** / **already fixed** → reject, citing the evidence or the decision.
- **spec question** → take the reading most faithful to the spec text, record it in the contract's `## Late decisions` marked "for the user to confirm", and fix to that reading if it changes behaviour.
- An accepted finding that leaves work for a later unit → `open` row in `spec/HANDOFFS.md` (`HO-<next> | NN | <unit> | <obligation> | open`), cited as `→ HO-<n>`.

Append the decisions as a round `(autonomous)` to `## Review resolutions` (create the section after `## Review` if missing; never edit earlier rounds):

```markdown
### Round <n> (autonomous) — YYYY-MM-DD HH:MM · against review fingerprint <fingerprint>
- [fixed → round <n+1>] <reviewer> <file:line> — <finding> → <planned fix>
- [accepted] <reviewer> <file:line> — <finding> → <reason, and where it is noted>
- [rejected] <reviewer> <file:line> — <finding> → <evidence>
```

**e. Decide whether to continue.**
- Verification passes and nothing is marked fix → done; go to step 3.
- Work list not empty and rounds remain → next round. Each fix stays inside its finding: no new guards, config couplings or checks the finding didn't ask for (on 06 a guard added by a fix became the next round's finding).
- The work list is the same as last round's, with no item closed → go straight to round 3 on `dev-implementer-max` rather than repeat the same model.
- Round 3 finished with work left → stop; go to step 3 and report what's left.

Record each round in the run log: what the implementer changed, verification counts, findings and decisions, and the tokens and duration each agent reported, in at most ten lines per agent.

## 3. Hand back

Never commit the implementation, push, merge or mark the row done: those are `/dev-6-final`, and they stay with the user.

**Log a stopped run.** Whenever the run ends **stopped** (a step 0 precondition, a spec contradiction, an environment problem, a denied prompt, round 3 with work left): `LEDGER record --repo . --unit NN-stopped-<reason slug> --kind stopped --since <time of the /dev-auto command, UTC ISO> --note "<why, one line>"`. A finished unit's cost is recorded by `/dev-6-final`.

**Hardening candidates.** If any were collected, ask the user once with AskUserQuestion (multiSelect, up to 4 per question, each with its cost/benefit line, "hand off" recommended unless the candidate is wrong-under-conditions): fix now, or hand off. Selected items → write each into the contract's `## Late decisions` with an exact definition (formula, keys or fields, what raises) and a robustness acceptance check tagged with its hazard; relaunch `spec-verification-writer` (denylist in place) to add checks for them; then one hardening round with `dev-implementer`, the runner and a focused re-review, even past the round cap. The rest → `open` rows in `spec/HANDOFFS.md`, or accepted with the reason when no later unit owns them. For every candidate, built or not, add one line `Register candidate: <hazard in one sentence>` to the run log, so `/dev-retro` can decide whether the hazard register should cover it next time. This is the only question the run asks.

Finish the run log with: rounds used, final verification counts, open findings, late decisions to confirm, handoffs added, and approximate tokens by agent. Then report to the user, in this order:
1. Outcome: **ready to finalize**, or **stopped** with the exact reason.
2. Late decisions to confirm: the choices you made that were the user's to make.
3. Accepted findings, with reasons, and the handoffs they created.
4. Token use by round, as reported by the agents.

End with one line:
- ready → `Next: /dev-6-final NN` (it re-checks the fingerprints, closes this unit's handoffs, records the ledger row and asks before every commit, push and merge)
- stopped → the one thing the user must decide or fix, then `/dev-auto NN` again to resume from the current branch.
