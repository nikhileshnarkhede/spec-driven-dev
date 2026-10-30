---
name: dev-retro
description: Retrospective over the workflow ledger — finds why units took extra rounds or tokens, proposes concrete edits to the dev-* commands, agents, templates or conventions, and applies only the ones the user approves. Run after every few finished units, e.g. /dev-retro or /dev-retro SCANIA_Project.
argument-hint: "[project] [--last N]"
disable-model-invocation: true
model: opus
effort: high
allowed-tools: Read Grep Glob Bash(python "${CLAUDE_SKILL_DIR}/../../scripts/usage_ledger.py" *) Bash(git log *) Bash(git diff *)
---

Work as the engineering manager running a blameless retrospective on the build process, not on the code: every extra round and every token spent is a symptom, and the goal is the smallest change to the workflow that removes its cause for future units. Evidence first; one recurring cause outweighs ten anecdotes.

Arguments: $ARGUMENTS — optional project name (default: all projects in the ledger) and `--last N` (default: units since the newest entry in `CHANGES.md`, at least 3).

## 1. Load the evidence

- `python "${CLAUDE_SKILL_DIR}/../../scripts/usage_ledger.py" render`, then read `~/.claude/workflow-metrics/LEDGER.md`, `ledger.jsonl` and `CHANGES.md`.
- For each unit in scope, read its `spec/NN-*/test-report.md` (`## Verification`, `## Review`, `## Review resolutions`, `## Autonomous run`) and the late decisions in its `contract.md`. The project folder is the repo whose name matches the ledger's project; ask if you can't find it.

## 2. Find the causes

Trace each round after the first to the finding or failure that forced it, and classify the cause:
- **spec gap**: the contract left a choice open, or two decisions conflicted → fix in `/dev-0-split` (what it should have asked) or in the templates.
- **test defect / writer–implementer disagreement**: the contract was ambiguous on an interface, error, tolerance or input source → fix in the contract template or the writer's instructions.
- **wrong behaviour / not built**: the implementer missed something stated → fix in the implementer's instructions or the unit size.
- **fragile hardening**: the reviewer wanted robustness beyond the spec → candidate for a convention or hazard (settled once, up front) instead of per-unit rounds. Read the run logs' `Register candidate:` lines: each names a hazard the register should have covered, so the next split writes it as a robustness check.
- **introduced by a fix**: a fix added something a later round flagged → fix-scope rules.
- **cost without rounds**: high main-session cost or peak context, expensive agent for small work, a model/effort mismatch with the work done → model, effort or session rules.

Count occurrences across units. Compare each unit's cost per 100 source lines and rounds with the units before and after each entry in `CHANGES.md`: did earlier changes work? Say plainly when the data is too thin (fewer than 3 units since a change) to judge.

## 3. Propose

At most 5 proposals, highest expected saving first. Each: the cause and its count, the exact file and edit (old → new text, short), the expected effect in rounds or cost units, and the risk (what quality it might cost). Prefer changes that move decisions earlier (split and contract) over changes that add review work later. Never propose weakening verification, independence of the test writer, or the user's confirmation gates.

Ask through AskUserQuestion (multiSelect) which to apply. Then also say which earlier changes, if any, should be reverted because the data shows they didn't help — ask before reverting.

## 4. Apply and record

Apply only the approved edits. Prepend each to `~/.claude/workflow-metrics/CHANGES.md`:

```markdown
**[YYYY-MM-DD] <one-line change>** — files: <paths>
- Evidence: <cause, count, units>
- Expected: <effect>; check after: <next 2–3 units>
```

Edit the workflow's source checkout — the repository this plugin was installed from — never the installed copy under `~/.claude/plugins/`, which is a versioned cache the next update replaces. `${CLAUDE_PLUGIN_ROOT}` is that checkout only when the marketplace was added from the local directory; otherwise ask for the path. After the edits, bump `version` in `.claude-plugin/plugin.json` and add the entry under `[Unreleased]` in `CHANGELOG.md`: installed copies receive the change through a release and `/plugin update`.

## 4b. Log this retro's own cost

`python "${CLAUDE_SKILL_DIR}/../../scripts/usage_ledger.py" record --repo . --unit retro-<YYYY-MM-DD> --kind retro --since <time you started, UTC ISO> --note "<changes applied or none>"`. The ledger's table of non-unit sessions (stopped runs, selects, retros) is what `/dev-retro` should read next time, so overhead outside units is counted too.

## 5. Report

The causes table (cause → count → units), what changed, what was declined, and what the next units should show if the changes work.
