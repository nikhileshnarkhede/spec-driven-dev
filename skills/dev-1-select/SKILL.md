---
name: dev-1-select
description: Step 1 — select the next sub-spec to work on — check it and its build contract are ready, create its branch, mark it in-progress, bring the contract up to date with the code that exists, and brief the user. Pass the sub-spec number, e.g. /dev-1-select 04. Implements nothing.
argument-hint: "<NN>"
disable-model-invocation: true
model: inherit
effort: low
allowed-tools: Bash(git status *) Bash(git log *) Bash(git diff *) Bash(git branch *) Bash(git rev-parse *) Bash(python "${CLAUDE_SKILL_DIR}/../dev-0-split/scripts/check_contracts.py" *) Bash(python "${CLAUDE_SKILL_DIR}/../dev-3-test/scripts/interface_surface.py" *) Bash(python "${CLAUDE_SKILL_DIR}/../../scripts/usage_ledger.py" *)
---

Work as a tech lead opening a work item: confirm it's ready to start, set it up cleanly, and hand the engineer a brief that makes planning fast. Implementation stays with the user.

Sub-spec: $ARGUMENTS (if empty, ask which one).

## 1. Check it's ready

Read `spec/INDEX.md`, `spec/NN-*/sub-spec.md` and `spec/NN-*/contract.md`. If the index doesn't exist, tell the user to run `/dev-0-split` first and stop.

- **Status.** If the row is `in-progress`, ask whether to resume its existing branch or restart; never create a second branch for the same sub-spec. If it's `done` or `pre-existing`, say so and ask whether they really mean to reopen it.
- **Dependencies.** Every entry in `Depends on` must be `done` or `pre-existing`. If one isn't, stop and name it — building on an unfinished foundation is what the dependency column exists to prevent. The user may override, for example to build against an interface they know is stable, but only explicitly.
- **Contract.** Run:
  ```
  python "${CLAUDE_SKILL_DIR}/../dev-0-split/scripts/check_contracts.py" spec --unit NN --stage start
  ```
  - No `contract.md`: recommend running `/dev-0-split` first. Its upgrade mode writes the contract, and settling the decisions up front is what lets the unit pass in one round. Ask whether to stop for that or continue without a contract.
  - An open decision, or a header question with no decision: settle each now through AskUserQuestion (options, your recommendation first) and write the answer into the contract's `## Decisions` as `[decided] … By: user, <date>`.
  - Any other ERROR: show it and fix the contract with the user before going on.
- **Working tree.** Run `git status`. If `spec/` itself is untracked, the baseline commit from `/dev-0-split` never happened: offer it now (run `no-claude-footprint` first, stage `Complete spec/` and `spec/` by name, commit on the main branch with no attribution line). Any other uncommitted change that isn't part of this sub-spec: stop and ask rather than carrying it onto the new branch.

## 2. Set up

From the main branch (confirm its name if ambiguous), create and check out `subspec/NN-<slug>`. Set the row to `in-progress` in `spec/INDEX.md` and commit that change alone: `start NN: <title>`, no attribution line.

## 3. Bring the contract up to date

Contracts are written when the spec is split, before the units they depend on exist. Before anyone plans against this one, check it against what was really built:
- **Incoming handoffs.** Every `open` row in `spec/HANDOFFS.md` addressed to this unit must be listed under `## Incoming handoffs`, each mapped to the acceptance check that discharges it; add an acceptance check where none covers it.
- **Inputs.** For each existing function the Interfaces section names as an input source, confirm it exists with that signature (`python "${CLAUDE_SKILL_DIR}/../dev-3-test/scripts/interface_surface.py" <files>`). Where the built code differs, correct the contract and say what changed, and log it against the unit that built it: `python "${CLAUDE_SKILL_DIR}/../../scripts/usage_ledger.py" escaped --unit <earlier unit> --found-in NN --kind spec-gap --note "<what differed>"`.
- **Accepted limitations.** Read the dependencies' entries in `CLAUDE.local.md` and their `## Review resolutions`. A limitation that affects this unit and isn't in the contract becomes a risk or a decision; ask the user about anything that changes behaviour.
- **Locked tests touched.** The contract's `Extends:` lines name the earlier functions this unit changes or extends (new reads, new required inputs, changed output shape); also grep the dependencies' `test_subspec_*` files for calls to them. Where those checks fake the function through `tests/stubs/`, the fix is a stub update under this unit, not an edit of the locked file: plan it. Where a locked file's own stub, fixture or assertion would break, ask the user now whether that file may get stub/fixture updates with every assertion kept (or name the assertion the contract contradicts), and record the answer as a decision `D<n>` naming the files. Locked files are otherwise edited only on the user's say-so.

Re-run the contract check until it passes, and leave the contract edits uncommitted: they belong to this unit's change and are committed with it by `/dev-6-final`.

## 4. Brief

Give the user, in this order:
1. Scope: what the unit builds and what it must leave to other units.
2. The decisions already settled, in one line each, and anything you changed in step 3.
3. The acceptance checks: these are the definition of done, and `/dev-3-test` turns each into at least one test.
4. The risks to design against.
5. That `spec/NN-<slug>/test-report.md` will collect the verification and review results.
6. The next step, on its own last line: `Next: /dev-2-write NN`. It fixes the interfaces in the contract, gets the plan approved, and only then writes code. For an unattended run, use `/dev-auto NN` instead. Run each unit in a fresh session: every call re-reads the whole conversation, and carried-over work made 06's coordinator two-thirds of its cost (`~/.claude/workflow-metrics/LEDGER.md`).

Then stop. Don't plan or write implementation code here. If the select ended without a branch (blocked by a dependency, an open decision, or the user stopping), log the session's cost: `python "${CLAUDE_SKILL_DIR}/../../scripts/usage_ledger.py" record --repo . --unit NN-select-<slug> --kind select --note "<why>"`.
