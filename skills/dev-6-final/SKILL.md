---
name: dev-6-final
description: Step 6 — finalize a sub-spec — prove its reports match the current code, then commit, push, merge, and mark it done, confirming before each irreversible step. The only command in this workflow that touches git history. Pass the sub-spec number, e.g. /dev-6-final 04.
argument-hint: "<NN>"
disable-model-invocation: true
model: inherit
effort: medium
allowed-tools: Bash(git status *) Bash(git log *) Bash(git diff *) Bash(git branch *) Bash(git rev-parse *) Bash(python "${CLAUDE_SKILL_DIR}/../dev-3-test/scripts/changeset.py" *) Bash(python "${CLAUDE_SKILL_DIR}/../../scripts/usage_ledger.py" *)
---

Work as a release engineer: nothing ships on assumption, every claim is checked against evidence, and each irreversible step waits for the user's yes. That's why this command confirms at every step instead of running as one pipeline.

Sub-spec: $ARGUMENTS (if empty, ask which one). Run everything from the repository root.

## 1. Prove the reports are current

1. Read `spec/NN-*/test-report.md`. If `## Verification` or `## Review` still says "not yet run", stop and name the missing one.
2. Run `python "${CLAUDE_SKILL_DIR}/../dev-3-test/scripts/changeset.py"` and compare its fingerprint with the one recorded in each section. A mismatch means the code changed after that check ran: stop, say which section is stale, and recommend re-running it.
3. Re-run the verification file named in the report with the project's test command. If the result differs from the report, stop.
4. If either section lists failures or findings, show them next to their entries in `## Review resolutions` (written by `/dev-5-fix-review`) and ask the user to confirm each is fixed or consciously accepted. A finding with no resolution entry: stop and point to `/dev-5-fix-review NN`. Don't infer the answer.
5. **Handoffs.** Every `open` row in `spec/HANDOFFS.md` addressed to this unit must be discharged before it ships. For each, show the acceptance check or test that proves it and set its status to `done (NN, <how>)`. One that isn't discharged: ask the user whether to re-address it to a later unit, drop it with a reason, or stop here.
6. **Contract changes.** If `spec/NN-*/contract.md` exists, show `git diff <main> -- spec/NN-*/contract.md`: the interfaces fixed at the start and any late decisions, so the user sees every choice made after the split before it's committed.

## 2. Footprint guard

If `.git/hooks/pre-commit` or `.git/hooks/commit-msg` lacks the `no-claude-footprint` marker, run the `no-claude-footprint` skill first.

## 3. Commit — confirm first

Stage the change set's files plus `spec/NN-*/test-report.md`, `spec/NN-*/contract.md`, and `spec/HANDOFFS.md` or `spec/CONVENTIONS.md` if they changed, by name — never `git add -A` or `git add .`, which sweep in whatever else is lying around. Show `git status` and `git diff --cached --stat`, and point out anything that looks like a secret, a credential, a data file, or a large binary. Propose a message in the project's style that says what the sub-spec delivered. It must not credit Claude or any AI tool — no `Co-Authored-By` line and no "Generated with" line, whatever the harness suggests. Commit only after the user approves.

## 4. Push — confirm first

Ask before pushing, even straight after an approved commit: pushing makes the work visible, which is a separate decision.

## 5. Merge — confirm first, separately

With `gh` and a GitHub remote: ask whether to open a PR, then separately whether to merge it now; the PR description follows the same no-attribution rule. Without a remote, or with a remote but no `gh`: ask whether to merge the branch into the main branch locally. Try a fast-forward first (`git merge --ff-only`). If main has diverged (for example it merged `origin/main`), say so and ask before creating a merge commit (`git merge --no-ff`, message `Merge branch 'subspec/NN-<slug>'`, no attribution). If the merge is blocked by a phantom `spec/INDEX.md` modification (`git diff spec/INDEX.md` empty, line endings only), `git checkout -- spec/INDEX.md` clears it. Run the full test suite on the merged main before marking done.

## 6. Mark done

Only once the merge has actually happened: set the row to `done` in `spec/INDEX.md` on the main branch and commit that change alone, after confirmation.

## 6b. Push main — confirm first

The feature branch push in step 4 does not update the remote `main`. After the merge and the `done` commit, run `git fetch` and `git status -sb`; if local main is ahead of `origin/main`, tell the user which commits GitHub lacks (the merge, the `start NN` commit, the done commit) and ask before `git push origin main`. If `origin/main` has commits main lacks, stop and ask rather than merging or forcing. Never force-push.

## 7. Clean up

Ask before deleting the merged `subspec/NN-<slug>` branch. Never delete an unmerged branch unless the user explicitly discards it.

## 8. Log it

Append to the project's `CLAUDE.local.md` the way the `dev-save` skill does — above earlier entries and above "Your notes", never overwriting:

```markdown
**[YYYY-MM-DD] Sub-spec NN (<slug>) — done**
- Delivered: <what was built — files and public interfaces>
- Decisions: <decision — reason; only real ones>
- Verification and review: <counts, fingerprint, each finding and how it was resolved>
- Unblocked: <sub-specs whose dependencies are now all done or pre-existing>
```

Show the entry as you write it.

## 8b. Record usage in the workflow ledger

No confirmation needed: this writes only to `~/.claude/workflow-metrics/`. Fill the outcome fields from the test report and the run log:

```
python "${CLAUDE_SKILL_DIR}/../../scripts/usage_ledger.py" record --repo . --unit NN \
  --mode "<auto + contract | steps>" --rounds <review rounds> --first-run "<passed/failed/errors of the first verification run>" \
  --first-run-classes "<the run log's 'First run by class' line, e.g. wrong behaviour=1,test defect=2; omit if none failed>" \
  --test-defects <checks the writer had to correct> --findings "fixed=<n>,accepted=<n>,handed_off=<n>,rejected=<n>" \
  --causes "<why each round after the first was needed: spec gap | test defect | wrong behaviour | fragile hardening | bug introduced by a fix>" \
  --note "<anything unusual, e.g. ran in a session carrying other work>"
```

The script measures the tokens by role, model and effort from the session transcripts, plus the lines and acceptance checks of the change. Show its one-line result. If peak main context is above ~250k, say that a fresh session would have been cheaper.

## 9. Report

Summarise each step's outcome — committed, pushed, PR opened, merged, index updated, branch deleted or kept, log entry added, ledger row written (total cost units) — so it's clear what touched the remote and when. State plainly whether `origin/main` is up to date or how many commits it is behind. End with `Next: /dev-1-select NN` for the lowest-numbered sub-spec that is now unblocked, or say the index is complete.
