# Slice 02-status-filter: narrow `agy-mc status` listings

Kind: code · Round: 1 · Base commit: 843b73c696bcea76918740251ef1aca357665311
Repository: `<repo>` (work only inside it; all paths below are relative to it)

## Goal
`agy-mc status` without a job id accepts `--limit N` (the N most recently started jobs) and `--state S` (repeatable; keep jobs whose status is any of the given values). With neither flag, output is byte-for-byte what it is today.

## Context
- `antigravity_mission_control/cli.py` builds the parser: `status_parser = subparsers.add_parser("status", ...)` with one optional positional `job_id`.
- `antigravity_mission_control/jobs.py` `cmd_status`: with a job id prints that job; otherwise prints `{"jobs": list_jobs()}`. `list_jobs()` (jobstore.py) returns jobs sorted by `started_at` ascending, after `refresh_job`.
- Known statuses are the keys of `JOB_EXIT_CODES` in jobstore.py: done, done_with_warnings, starting, running, canceling, error, crashed, cancel_failed, canceled.
- Tests are `unittest.TestCase` classes. CI runs `python -m unittest discover -s tests -v` on a clean Python with **no pytest installed**, so do not import pytest. Existing suite: 68 tests.
- Existing tests redirect job storage by patching `antigravity_mission_control.jobstore.JOB_ROOT` (see tests/test_lifecycle.py and tests/test_job_state.py for the pattern). Writing `job.json` files for terminal jobs directly into a temporary JOB_ROOT is enough; no AGY process is needed.

## Scope
- May modify: antigravity_mission_control/cli.py, antigravity_mission_control/jobs.py, tests/test_status_filter.py (new)
- Must not touch: everything else (jobstore.py included)

## Steps
1. Add `--limit` (positive int) and `--state` (`action="append"`, `choices` = the known statuses) to the status parser.
2. In `cmd_status`: when a job id is given together with either flag, fail with a clear error (exit code 2 through argparse or a RuntimeError, your choice, but consistent with how the CLI reports usage errors). Otherwise filter by state first, then keep the last N (most recent), preserving ascending order.
3. `--limit 0` or negative is a usage error.
4. tests/test_status_filter.py: default output unchanged; --limit; --state (single and repeated); both combined; invalid limit; job id plus a flag.

## Acceptance
- [ ] behaviour as above; default `status` output unchanged
- [ ] help text of every other command unchanged
- Verification commands: `python3 -m unittest tests.test_status_filter -v` and `python3 -m unittest discover -s tests` (count must include the new tests)

## Skills
none
