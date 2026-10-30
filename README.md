# spec-driven-dev

Build a large project from one complete spec with [Claude Code](https://code.claude.com), one piece at a time. No piece reaches `main` without independent evidence that it does what the spec says.

A Claude Code plugin: ten slash commands, seven agents, three hooks and a usage ledger. Commands share the `/dev-` prefix and carry a step number, so typing `/dev-` lists them in order, and every command ends by printing the next one to run. The ledger records what every unit cost and why it needed each round, and `/dev-retro` turns that record into changes to the workflow itself.

```
Brainstorm ───/dev-spec──────► Complete spec/<name>.md + <name>-api-protocol.md
Complete spec ──/dev-0-split──► spec/INDEX.md, CONVENTIONS.md, HANDOFFS.md
                                + spec/NN-slug/{sub-spec.md, contract.md, test-report.md}
                                      │
          for each sub-spec, foundation first:
          ┌───────────────────────────────────────────────────────────────┐
          │ /dev-1-select NN       check contract → branch → refresh it   │
          │ /dev-2-write NN        interfaces → YOU APPROVE → code        │◄─┐ not built /
          │ /dev-3-test NN         a test per acceptance check, by agents │──┘ wrong behaviour
          │ /dev-4-review NN       two read-only reviewers in parallel    │──► clean? skip to 6
          │ /dev-5-fix-review NN   YOU DECIDE fix / accept / reject       │──► fixed? 3, then a
          │                                                               │    focused re-review
          │ /dev-6-final NN        prove reports current → commit → merge │
          └───────────────────────────────────────────────────────────────┘
          /dev-auto NN           steps 1–5 unattended, up to 3 rounds
          /dev-save              handoff note whenever you stop
          /dev-retro             every few units: what cost rounds, and which rule to change
```

**Read first:** [`docs/workflow-article.html`](docs/workflow-article.html) is a 5-minute illustrated overview (download it and open it in a browser). The full reference is [`docs/workflow-guideline.md`](docs/workflow-guideline.md).

## Why

- **Small pieces.** The spec is split into small sub-specs, each a word-for-word excerpt checked by a script, with dependencies tracked in an index.
- **Decide before you build.** Each sub-spec gets a build contract: ownership of every config key, the open questions and cross-section conflicts settled with you, exact interfaces, numbered acceptance checks and the risks to design against. The implementer, the test writer and both reviewers read the same contract, so they don't each guess differently. That mismatch is what usually forces a second round. A script checks every contract is complete before work starts.
- **Plan before code.** `/dev-2-write` writes nothing until you approve the interfaces and a plan mapping every acceptance check to the code.
- **Independent verification.** The test writer works from the spec and contract only, and a hook refuses its reads of the changed files. The runner can execute but not edit. Both reviewers are read-only with no shell. These limits are enforced by tool permissions and hooks, not just instructions.
- **Evidence over claims.** Each report records a fingerprint of the exact code it checked. `/dev-6-final` refuses to commit if the code changed afterwards.
- **Every finding gets an answer.** Each review finding is fixed, accepted with a reason, or rejected with evidence, and the answer is recorded. Obligations it leaves for later units go into a handoff ledger that those units must close.
- **Cheaper later rounds.** After fixes, a focused re-review checks the fixed findings and what changed since the last review instead of the whole change again.
- **Right model per step.** Opus for splitting, writing and the ML pipeline review; the session model elsewhere, with effort sized to each step.
- **Robustness is built in, not bolted on.** Each contract carries robustness checks derived from the project's hazard register, so hardening lands in round 1 instead of a third round after review.
- **Small units, enforced.** The contract check refuses more than 16 acceptance checks or 700 estimated source lines per unit, with no override, and refuses an index whose unit depends on a later-numbered one: units are numbered in dependency order, most independent first.
- **It learns from its own record.** `/dev-6-final` writes every finished unit to a global ledger (cost by role, model and effort; rounds; first-run failures by class; reviewer yield; escapes). `/dev-retro` reads it and proposes the smallest workflow change that removes a recurring cause; each change is logged with the evidence and the units to check it against.

## Contents

| Path | What |
|---|---|
| `skills/dev-spec`, `skills/dev-0-split` … `skills/dev-6-final`, `skills/dev-auto`, `skills/dev-save`, `skills/dev-retro` | The workflow commands, with helper scripts (`dev-0-split/scripts`, `dev-3-test/scripts`) and the contract templates (`dev-0-split/templates`) |
| `scripts/usage_ledger.py` | The usage ledger: measures a unit's cost from the session transcripts and renders `~/.claude/workflow-metrics/LEDGER.md`; called by `/dev-6-final`, `/dev-auto` and `/dev-retro` |
| `skills/no-claude-footprint` | Optional: keeps Claude Code files and AI attribution out of a repo's history via git hooks |
| `agents/` | `spec-verification-writer`, `spec-verification-runner`, `spec-compliance-reviewer`, `pipeline-risk-reviewer` and its re-review variant `pipeline-risk-reviewer-recheck`, plus `dev-implementer` and `dev-implementer-max` for `/dev-auto` |
| `.claude-plugin/` | `plugin.json` (the manifest and version) and `marketplace.json`, which makes this repository its own marketplace |
| `hooks/hooks.json` | Registers the three hooks below for every session the plugin is enabled in |
| `hooks/checkpoint-reminder.py` | Stop hook that reminds you to run `/dev-save` when you have unsaved progress |
| `hooks/guard-verification-file.py` | Blocks edits to the independent verification file, inside the implementer agents only (`agent_type` in the hook input) |
| `hooks/guard-writer-independence.py` | Refuses the test writer's reads of the files the change touched, inside that agent only |
| `docs/` | Illustrated article and full guideline |

## Unattended mode

`/dev-auto NN` runs select → implement → test → review → fix for one sub-spec in up to three rounds, without asking you anything. The implementer is Sonnet at high effort; Opus at xhigh is used only in round 3 and only for failing checks or confirmed defects the second round couldn't close. Hardening beyond the contract's robustness checks is collected and offered to you once, at the end, instead of being fixed round by round. Every decision it makes for you is written to the test report, and it stops before `/dev-6-final`, so commit, push and merge stay yours. It needs a complete contract and stops if a decision is still open, since that decision is yours. Details are in section 12 of the guideline.

## Install

Requirements: Claude Code 2.1 or later with access to Opus and Sonnet; git; Python 3 on your `PATH` as `python` (the hooks and scripts call it by that name); your project's test framework (the examples use pytest); `gh` only if you want `/dev-6-final` to open PRs.

In Claude Code:

```
/plugin marketplace add nikhileshnarkhede/spec-driven-dev
/plugin install spec-driven-dev@nikhileshnarkhede
```

That's the whole install: the commands appear as `/dev-…` (also as `/spec-driven-dev:dev-…`), the agents and the three hooks register themselves, and `/plugin update` brings in each release. The usage ledger is written to `~/.claude/workflow-metrics/` on the first `/dev-6-final`.

To work on the workflow itself, clone the repository and add your checkout as the marketplace instead (`/plugin marketplace add /path/to/spec-driven-dev`): Claude Code then loads the plugin in place, and edits take effect after `/reload-plugins`.

## Quick start

1. In your project: `git init` (if needed). Either put your finished spec in `Complete spec/<name>.md`, or run `/dev-spec` to turn a brainstorm into an API protocol and a spec whose sections are already the units, in dependency order.
2. `/dev-0-split`: confirm the proposed split and build order, answer its decision questions, then accept the baseline commit. On a project split with an earlier version, running it again adds the contracts without re-splitting.
3. For each sub-spec, one fresh session each: `/dev-1-select NN` → `/dev-2-write NN` → `/dev-3-test NN` → `/dev-4-review NN` → `/dev-5-fix-review NN` → `/dev-6-final NN`, or `/dev-auto NN` → `/dev-6-final NN`.
4. Stopping mid-way: `/dev-save`. Next time, run the command on its `Resume:` line in `CLAUDE.local.md`.
5. Every few units: `/dev-retro`. It reads the ledger and proposes changes to the commands; you approve each one.

The step commands only run when you type them (`disable-model-invocation`). Every commit, push, merge and branch deletion waits for your explicit yes.

## Notes

- The pipeline-risk reviewer and the hazard register in `dev-0-split/templates/CONVENTIONS.md` are written for ML and data-pipeline code: leakage, evaluation integrity, train/eval mode, nondeterminism. For other domains, adapt the register (the split does this per project) and the reviewer's checklist.
- Progress notes go to `CLAUDE.local.md` in your project. Keep that file gitignored; it's your private log.

## License

[MIT](LICENSE): free to use, copy, modify and distribute, including for commercial use, as long as the copyright notice and license text are kept.

## Author

Nikhilesh Narkhede: [portfolio](https://nikhileshnarkhede.github.io/portfolio/) · [GitHub](https://github.com/nikhileshnarkhede) · [LinkedIn](https://www.linkedin.com/in/nikhileshnarkhede/)
