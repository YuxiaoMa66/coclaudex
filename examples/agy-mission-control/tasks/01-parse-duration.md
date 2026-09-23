# Slice 01-parse-duration: shared duration parser

Kind: code · Round: 2 · Base commit: 0fc10c83c62def2c077de308e1aef71447230390
Repository: `<repo>` (work only inside it; all paths below are relative to it)

## Goal
`antigravity_mission_control.common.parse_duration(text) -> float` returns seconds, and `cmd_wait` uses it with unchanged behavior.

## Context
- `antigravity_mission_control/jobs.py` `cmd_wait` currently parses `--timeout` inline with `re.fullmatch(r"(\d+(?:\.\d+)?)(ms|s|m|h)", ...)` and raises `RuntimeError('Invalid --timeout; use values such as 100s, 5m, or 1h')`, then `RuntimeError("--timeout must be positive")` when the value is <= 0.
- A later slice will reuse the parser for `prune --older-than`, which also needs a `d` (days) unit.
- Tests are `unittest.TestCase` classes. CI runs `python -m unittest discover -s tests -v` on a clean Python with no pytest installed, so tests must not import pytest. Existing suite: 64 passed.

## Scope
- May modify: antigravity_mission_control/common.py, antigravity_mission_control/jobs.py, tests/test_duration.py (new)
- Must not touch: everything else

## Steps
1. Add `parse_duration(text: str) -> float` to common.py. Units: ms, s, m, h, d. Accept integer or decimal numbers. Raise `ValueError` with a message naming the bad value for anything else (empty, missing unit, unknown unit, negative sign, spaces).
2. In `cmd_wait`, call it and keep the exact existing RuntimeError messages for invalid and non-positive values (`0s` is still "must be positive"). `--timeout-seconds` stays as is.
3. tests/test_duration.py: valid units incl. decimals and `d`; the invalid cases above; one test that `wait --timeout nonsense` still reports the old message (drive `cmd_wait` directly or via the CLI, whichever is simpler).

## Acceptance
- [ ] parse_duration handles ms/s/m/h/d, rejects malformed input with ValueError
- [ ] `wait` error messages unchanged
- Verification commands: `python3 -m unittest tests.test_duration -v` and `python3 -m unittest discover -s tests` (the "Ran N tests" count must include the new tests)

## Skills
none

## Rework (round 2)
Your previous round's changes are still uncommitted in the working tree; build on them, do not start over. The orchestrator confirmed these findings. Fix every one of them:
- O1 [blocker] tests/test_duration.py — written for pytest, but CI runs `python -m unittest discover -s tests` without pytest: the module fails to import there, and where pytest is installed the 14 tests are silently skipped ("Ran 64 tests"). → Rewrite as `unittest.TestCase` with `subTest` for the parameter cases and `assertRaisesRegex`; no pytest import.
- F2 [minor] tests/test_duration.py — add a test that `wait` with timeout `0s` raises RuntimeError "--timeout must be positive".
(The orchestrator's round-1 handoff wrongly said the tests run with pytest; the Context and commands above are corrected.)
