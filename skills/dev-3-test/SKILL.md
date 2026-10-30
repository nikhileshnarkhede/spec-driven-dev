---
name: dev-3-test
description: Step 3 — test the current sub-spec against its own text and build contract — derive independent checks from the acceptance checks (not the code), run them, triage every failure, and record the result against the exact code state. Pass the sub-spec number, e.g. /dev-3-test 04.
argument-hint: "<NN>"
disable-model-invocation: true
model: inherit
effort: medium
allowed-tools: Bash(git status *) Bash(git log *) Bash(git diff *) Bash(git branch *) Bash(git rev-parse *) Bash(python *)
---

Work as a QA lead running independent verification. Whoever writes the checks must not know how the code works, whoever runs them must not be able to change them, and the result is recorded against the exact code state it describes.

Sub-spec: $ARGUMENTS (if empty, ask which one). Run everything from the repository root.

## 1. Gather the evidence

1. Read `spec/NN-*/sub-spec.md` and `spec/NN-*/contract.md`. If the contract exists, it must pass:
   ```
   python "${CLAUDE_SKILL_DIR}/../dev-0-split/scripts/check_contracts.py" spec --unit NN --stage test
   ```
   If it fails, stop and show the errors: the writer needs fixed interfaces and settled decisions, otherwise its checks are guesses. (`/dev-2-write NN` fixes the interfaces.)
2. Compute the change set — everything this branch changed since it left the main branch, committed or not, new untracked files included:
   ```
   python "${CLAUDE_SKILL_DIR}/scripts/changeset.py"
   ```
3. Work out the project's test setup with Glob and Read: the test directory that serves the code in the change set (where `conftest.py` or existing `test_*.py` files live), the framework, its import conventions, and the exact command that runs a single test file from the right working directory. Ask only if it's genuinely ambiguous.
4. The verification file is `<test dir>/test_subspec_NN_<slug_with_underscores>.py`.
5. Extract the interface surface — signatures only, no bodies or constant values — of the change set's non-test Python files:
   ```
   python "${CLAUDE_SKILL_DIR}/scripts/interface_surface.py" <files>
   ```
   For other languages, collect declaration lines with Grep instead.

## 2. Write the checks (only if the verification file doesn't exist)

If the file exists, keep it — someone may have edited it on purpose — unless the user asks for a fresh one.

Otherwise launch `spec-verification-writer` with: the sub-spec path, the contract path, `spec/CONVENTIONS.md`, the interface surface pasted in full, the test framework, the import conventions, a conftest or fixture file to reuse if there is one, the project's `tests/stubs/` module if it exists, and the exact file path to write. Don't name the implementation files, the implementer's tests, or describe how the code works; the writer's independence from the implementation is the point, and the contract gives it everything it needs to call the code.

Every time the writer is launched (here, or to correct a check), first write the change set's file paths, one per line as `changeset.py` printed them, to `<git-dir>/verification-writer-denylist`; delete that file as soon as the writer returns. While it exists, the writer's hook refuses reads of those files, so its checks can't quietly mirror the implementation.

## 3. Run and triage

Launch `spec-verification-runner` with: the verification file path, the exact command that runs it, the command that runs the project's full test suite, and the contract path (so it can map each failure to its acceptance check and tell an interface mismatch from a test defect).

## 4. Record

Show the user the runner's report unchanged, failures included. Re-run `changeset.py` for the fingerprint of the code as tested (the verification file now exists, so it differs from step 1), then replace only the `## Verification` section of `spec/NN-*/test-report.md`:

```markdown
## Verification
_Last run: YYYY-MM-DD HH:MM · change-set fingerprint: <fingerprint> · file: <verification file path>_

<N passed / M failed / K errors> · regressions elsewhere: <none, or list>

- [PASS] AC<n> <check> — <source: §x / D<n> / C<n>>
- [FAIL · <not built | wrong behaviour | test defect | spec contradiction | environment>] AC<n> <check> — observed: <value>

Acceptance checks without a test, and spec statements without a check:
- AC<n> / §x: "<statement>" — <reason>
```

Leave `## Review` and `## Review resolutions` as they are. Before the `Next` line, give a three-line checkpoint so the user always knows where the unit stands: **Done** (this stage, one line) · **Changed** (files touched, or none) · **Decided** (decisions made here, or nothing new).

Say what each failure class means for the next step — `not built` and `wrong behaviour` (including code that doesn't match the contract's interfaces) go back to the implementation, `test defect` back to the checks, `spec contradiction` to the user — and end with one line:
- everything passes → `Next: /dev-4-review NN`
- `not built` or `wrong behaviour` → `Next: /dev-2-write NN` (continue the implementation), then `/dev-3-test NN` again
- otherwise → name the decision the user has to make before re-running `/dev-3-test NN`
