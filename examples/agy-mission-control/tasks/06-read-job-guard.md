# Slice 06-read-job-guard: reject malformed status where job metadata is read

Kind: code · Round: 1 · Base commit: 0d4a8a280ffb3e8334eeb5f85f88ef6f7253d261
Repository: `<repo>` (work only inside it; all paths below are relative to it)

## Goal
`jobstore.read_job` rejects job metadata whose `status` is present but not a string, so every command that reads a job (status, status <id>, wait, cancel, continue, prune, the background worker, launch) reports a clean error instead of raising TypeError.

## Context
- `antigravity_mission_control/jobstore.py` `read_job` already raises `RuntimeError(f"Job metadata must be an object: {path}")` for non-object JSON. The CLI's `main` turns RuntimeError into `{"status": "ERROR", "error": ...}` on stderr and exit code 1; `list_jobs` skips entries that raise RuntimeError; prune reports them under "skipped" with the error text as reason.
- Today `agy-mc continue <id> --prompt-file f` on a job.json with `"status": ["done"]` raises `TypeError: unhashable type: 'list'` (jobs.py:710, approvals.py:100). The worker (jobs.py:396/415) and launch (jobstore.py:363) have the same pattern. All of them read through read_job.
- A missing status (`None`) is hashable and handled elsewhere: do not reject it.
- The isinstance guards added in slice 05 (jobs.py `_exit_code`, `_prune_reason`, cmd_cancel, cmd_wait; refresh_job) stay as they are.
- Existing tests that write `"status": ["done"]` into job.json and expect it to be listed, shown, or skipped with reason "unknown status" will now see the read_job error instead. **You may update those expectations** in tests/test_malformed_status.py and tests/test_prune.py to the new behaviour (not listed by status; `status <id>`, cancel, wait, continue print the ERROR envelope and exit 1; prune skips with the read_job error as reason and still removes a valid old job next to it). Do not weaken any other assertion.
- Tests are `unittest.TestCase`; CI runs `python -m unittest discover -s tests -v` without pytest. Suite: 102 tests.

## Scope
- May modify: antigravity_mission_control/jobstore.py, tests/test_malformed_status.py, tests/test_prune.py, CHANGELOG.md
- Must not touch: everything else

## Steps
1. read_job: after the object check, if `"status"` is present and not a str, raise `RuntimeError(f"Job metadata has an invalid status: {path}")`.
2. Update the affected test expectations as described above.
3. Add tests: `continue` on a list status prints the ERROR envelope and exits 1 without a traceback (run the CLI with `python3 -m antigravity_mission_control.cli` and AGY_MC_JOB_ROOT pointing at a temp dir, as test_malformed_status already does); `cancel` likewise.
4. CHANGELOG.md: extend the existing Unreleased `Fix:` line for malformed statuses to say every command now reports them as an error.

## Acceptance
- [ ] no TypeError from any command on a list status
- Verification commands: `python3 -m unittest tests.test_malformed_status tests.test_prune -v`, `python3 -m unittest discover -s tests`, `python3 -m compileall -q antigravity_mission_control scripts tests`

## Skills
none
