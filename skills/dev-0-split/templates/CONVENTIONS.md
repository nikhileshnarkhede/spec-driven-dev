# Project conventions

Decided once for every sub-spec, so nobody re-decides them per unit. Implementers follow them, test writers may assume them, reviewers don't flag code that follows them. Contracts cite them as `C<n>` and `HZ<n>`. Change one only by editing this file, which applies to every unit not yet built.

## Conventions
- C1 Configuration: every tunable value (number, path, name, toggle) is read from the project's config module; code keeps only validation vocabularies (lists of allowed strings). A value that experiments can override is read when it is used, not copied at import.
- C2 Errors: invalid configuration or input raises `ValueError` naming the key or argument, the bad value and what is accepted. No silent fallback, no swallowed exception, no warn-and-continue for anything that changes results. Raise at start-up, before data loads, when the problem can be detected then.
- C3 Numerics: tensors and model outputs are float32 unless the spec says otherwise; statistics accumulated over a dataset are float64. Thresholds follow the spec's inclusive/exclusive wording; "improves" means strictly better (`<` for a loss). A standard deviation is the sample one (ddof = 1) unless the spec says population.
- C4 Units: every public array or tensor states its unit in the docstring. Scaling is applied in one function and undone in one function; reported numbers are in the spec's unit.
- C5 Randomness: every random draw comes from an explicitly seeded generator passed in or derived from the run seed; the same seed gives identical results to 6 decimals. Nothing draws random numbers at import.
- C6 Purity: functions don't mutate their inputs or shared config; they return new objects.
- C7 Persistence: files are written atomically (temporary file, then rename). Anything that changes a model's outputs is saved with it (state or resolved config), so a reload reproduces the outputs exactly.
- C8 Public API: public functions and classes have type hints and a docstring stating shapes, dtypes, units and what they raise. Names follow the spec's wording.
- C9 Tests: the implementer's unit tests live next to the existing tests in `test_<module>.py`; the file `test_subspec_NN_<slug>.py` belongs to the independent test writer and is never edited by the implementer. Tests use small synthetic data and fixed seeds; anything slow is marked with the project's slow marker. Stubs and fakes for another unit's interface live in `tests/stubs/<unit-slug>.py`, owned by the unit that owns the interface; a later unit that changes the interface updates the stub there under a recorded decision instead of editing a locked `test_subspec_*` file, and independent checks never pin another unit's defaults or signatures beyond what their own contract states.
- C10 Logging: library code logs through the project logger and never prints.
- C11 Readability: code is written for a developer who will edit it by hand — plain control flow, short functions with descriptive names, the idioms and layout of neighbouring modules, no metaprogramming or abstraction layers the spec doesn't need. Hand edits by the user are authoritative: later runs build around them and never revert them.

## Hazard register
Failure modes that silently produce wrong numbers. A contract lists the ones that apply to its unit as risks (`R<n> [HZ<n>]`), each with the required behaviour and the check that proves it.
- HZ1 Leakage: anything fitted (scalers, encoders, statistics, calibration maps, thresholds) uses training data only and is reused unchanged elsewhere; held-out data never reaches training, early stopping or model selection.
- HZ2 Causality: no value at prediction point t uses information after t (features, padding, convolution, attention, targets).
- HZ3 Units and scaling: a value is scaled exactly once and unscaled exactly once; comparisons and thresholds use operands in the same unit.
- HZ4 Train/eval mode: dropout, normalisation and sampling modes are set explicitly at every entry point (training, evaluation, inference), never inherited by accident.
- HZ5 Determinism: seeding happens before anything draws random numbers (including plug-in imports and data-loader workers); per-entity seeds don't collide.
- HZ6 Degenerate inputs: empty selections, all-censored or all-missing batches, a batch with nothing to learn from, NaN or Inf in padded positions — each has a defined result (exact 0, skip, or a clear error), never NaN.
- HZ7 Dtype and device: no silent float64↔float32, integer division or CPU/GPU mixing; thresholds computed in reduced precision (bf16/fp16) are checked or avoided.
- HZ8 Saved state: everything that changes outputs survives save and load; loading a mismatched artifact raises instead of mis-wiring. Every written artifact records the sha256 (or config hash) of the inputs it was derived from, and loading refuses a mismatch; loading validates array contents (matching lengths, finite values, required ordering); an output that a rerun will replace is removed before its inputs are re-read, so a failed rerun can't leave a stale file beside new inputs.
- HZ9 Stale configuration: values derived from config at import time go stale under experiment overrides; derive them at use time or recompute them with the overrides.
- HZ10 Plug-in safety: plug-ins receive only the keys they declare (never labels unless they are a loss term), their names and order are recorded, and the framework doesn't overwrite their initialisation.
- HZ11 Boundaries: inclusive/exclusive edges, off-by-one windows, padding side and the first real step are checked at and either side of each edge.
- HZ12 Relaxed gates: no threshold, assertion or check is loosened, removed or caught-and-ignored without a recorded decision.
