# contract-driven-dev

Build a large project from one complete spec with [Claude Code](https://code.claude.com), one piece at a time. No piece reaches `main` without independent evidence that it does what the spec says.

A Claude Code plugin: eleven slash commands (plus the optional `/no-claude-footprint`), seven agents, four hooks and a usage ledger. Commands share the `/dev-` prefix and carry a step number, so typing `/dev-` lists them in order, and every command ends by printing the next one to run. The ledger records what every unit cost and why it needed each round, and `/dev-retro` turns that record into changes to the workflow itself.

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

**Read first:** the [5-minute illustrated overview](https://nikhileshnarkhede.github.io/spec-driven-dev/) (source: [`docs/workflow-article.html`](docs/workflow-article.html)). The full reference is the [guideline](https://nikhileshnarkhede.github.io/spec-driven-dev/workflow-guideline.html) (source: [`docs/workflow-guideline.md`](docs/workflow-guideline.md)).

## Why

- **Decide before you build.** Each sub-spec gets a build contract (config-key ownership, settled decisions, exact interfaces, numbered acceptance checks, risks), and a script refuses to start a unit whose contract is incomplete or too big. Implementer, test writer and both reviewers read the same contract, so they don't each guess differently.
- **Independent verification.** The test writer works from the spec and contract only; the runner can execute but not edit; both reviewers are read-only. Tool permissions and hooks enforce this, not just instructions.
- **Evidence over claims.** Reports carry a fingerprint of the code they checked, and `/dev-6-final` refuses to commit if the code changed afterwards. Every review finding is fixed, accepted with a reason or rejected with evidence.
- **One environment.** The suite and the application run in the project's container; counts name the image and every skip carries its reason.
- **It learns from its own record.** A usage ledger records what every unit cost and why it needed each round, and `/dev-retro` proposes the smallest workflow change that removes a recurring cause.

The full list of rules is section 8 of the guideline.

## Contents

| Path | What |
|---|---|
| `skills/dev-spec`, `skills/dev-0-split` … `skills/dev-6-final`, `skills/dev-auto`, `skills/dev-save`, `skills/dev-retro` | The workflow commands, with helper scripts (`dev-0-split/scripts`, `dev-3-test/scripts`) and the contract templates (`dev-0-split/templates`) |
| `scripts/usage_ledger.py` | The usage ledger: measures a unit's cost from the session transcripts and renders `~/.claude/workflow-metrics/LEDGER.md`; called by `/dev-6-final`, `/dev-auto` and `/dev-retro` |
| `skills/no-claude-footprint` | Optional: keeps Claude Code files and AI attribution out of a repo's history via git hooks |
| `agents/` | `spec-verification-writer`, `spec-verification-runner`, `spec-compliance-reviewer`, `pipeline-risk-reviewer` and its re-review variant `pipeline-risk-reviewer-recheck`, plus `dev-implementer` and `dev-implementer-max` for `/dev-auto` |
| `.claude-plugin/` | `plugin.json` (the manifest and version) and `marketplace.json`, which makes this repository its own marketplace |
| `hooks/hooks.json` | Registers the four hooks below for every session the plugin is enabled in |
| `hooks/checkpoint-reminder.py` | Stop hook that reminds you to run `/dev-save` when you have unsaved progress |
| `hooks/record-session.py` | Stop hook that records the session's transcript path for the usage ledger, so the ledger reads only transcripts it was told about |
| `hooks/guard-verification-file.py` | Blocks edits to the independent verification file, inside the implementer agents only (`agent_type` in the hook input) |
| `hooks/guard-writer-independence.py` | Refuses the test writer's reads of the files the change touched, inside that agent only |
| `docs/` | Illustrated article and full guideline |

## Unattended mode

`/dev-auto NN` runs steps 1 to 5 for one sub-spec in up to three rounds without asking you anything, and stops before `/dev-6-final`, so commit, push and merge stay yours. It needs a complete contract. See section 11 of the guideline.

## Docker

The suite and the application run in a container the project ships; a repository without one gets it as its first unit from `/dev-0-split`. Recipe, GPU variant and Windows notes: guideline section 6, "Docker".

## Install

Requirements: Claude Code 2.1 or later with access to Opus and Sonnet; git; Python 3 on your `PATH` as `python` (the hooks and scripts call it by that name); your project's test framework (the examples use pytest); Docker, since the suite and the application run in the project's container (guideline section 6); `gh` only if you want `/dev-6-final` to open PRs.

In Claude Code (the repository keeps its original name, `spec-driven-dev`; the plugin is `contract-driven-dev`):

```
/plugin marketplace add nikhileshnarkhede/spec-driven-dev
/plugin install contract-driven-dev@nikhileshnarkhede
```

That's the whole install: the commands appear as `/dev-…` (also as `/contract-driven-dev:dev-…`), the agents and the four hooks register themselves, and `/plugin update` brings in each release. The usage ledger is written to `~/.claude/workflow-metrics/` on the first `/dev-6-final`.

The plugin is distributed from this repository's own marketplace, not from Claude's plugin directory. The directory accepts command hooks, scripts and files other than Markdown only from organizations it has verified, and this plugin's guarantees rest on exactly those: hooks that keep the test writer and the implementers apart, the contract and fidelity checks, the change-set fingerprint and the usage ledger. Rather than ship a version without them, it stays here, whole.

To work on the workflow itself, clone the repository and add your checkout as the marketplace instead (`/plugin marketplace add /path/to/spec-driven-dev`): Claude Code then loads the plugin in place, and edits take effect after `/reload-plugins`.

## Quick start

1. In your project: `git init` (if needed). Either put your finished spec in `Complete spec/<name>.md`, or run `/dev-spec` to turn a brainstorm into an API protocol and a spec whose sections are already the units, in dependency order.
2. `/dev-0-split`: confirm the proposed split and build order, answer its decision questions, then accept the baseline commit. On a project split with an earlier version, running it again adds the contracts without re-splitting.
3. For each sub-spec, one fresh session each: `/dev-1-select NN` → `/dev-2-write NN` → `/dev-3-test NN` → `/dev-4-review NN` → `/dev-5-fix-review NN` → `/dev-6-final NN`, or `/dev-auto NN` → `/dev-6-final NN`.
4. Stopping mid-way: `/dev-save`. Next time, run the command on its `Resume:` line in `CLAUDE.local.md`.
5. Every few units: `/dev-retro`. It reads the ledger and proposes changes to the commands; you approve each one.

The step commands only run when you type them (`disable-model-invocation`). Every commit, push, merge and branch deletion waits for your explicit yes.

## Data handling

Nothing leaves your machine. The plugin makes no network calls, reads no credentials and has no MCP servers.

- **Hooks** (`hooks/`): four local Python scripts. Two guards inspect the file path of a Read, Grep, Write or Edit call to keep the test writer away from the code under test and implementers away from the verification file; a Stop hook checks the age of `CLAUDE.local.md` and `git status`; the other Stop hook writes the session's id, working directory and transcript path to `~/.claude/workflow-metrics/sessions.jsonl` (one line per session) so the ledger knows which transcripts to read. The guards and the reminder store nothing.
- **Git**: the commands run `git` in your repository, and `gh` or `git push` only when you confirm it in `/dev-6-final`.
- **Usage ledger** (`scripts/usage_ledger.py`): reads only the session transcripts that the Stop hook registered (it never searches `~/.claude` on its own; a session from before the plugin was installed is added with `record --transcript <path>`) for token counts, model names, timestamps, working directories and agent names, plus `git log` and `git diff --numstat` of your repository, and writes the result to `~/.claude/workflow-metrics/`. It never reads message text for anything but slash-command names and arguments, and nothing is sent anywhere. The ledger exists so that `/dev-retro` can tune the commands and agents from what each one actually costs.
- **Files written in your project**: `Complete spec/` (by `/dev-spec`, with your approval), `spec/` (sub-specs, contracts, test reports, the handoff ledger), the code and tests you approve, `CLAUDE.local.md` (a private log you keep gitignored), and `.git/verification-writer-denylist` while a test run is in progress.

## Notes

- The pipeline-risk reviewer and the hazard register in `dev-0-split/templates/CONVENTIONS.md` are written for ML and data-pipeline code: leakage, evaluation integrity, train/eval mode, nondeterminism. For other domains, adapt the register (the split does this per project) and the reviewer's checklist.
- Progress notes go to `CLAUDE.local.md` in your project. Keep that file gitignored; it's your private log.

## License

[MIT](LICENSE): free to use, copy, modify and distribute, including for commercial use, as long as the copyright notice and license text are kept.

## Author

Nikhilesh Narkhede: [portfolio](https://nikhileshnarkhede.github.io/portfolio/) · [GitHub](https://github.com/nikhileshnarkhede) · [LinkedIn](https://www.linkedin.com/in/nikhileshnarkhede/)
