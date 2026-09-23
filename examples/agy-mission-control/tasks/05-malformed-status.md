# Slice 05-malformed-status: survive malformed job and result files

Kind: code · Round: 2 · Base commit: af605979a53abc0dd5cc78b35784eb8c92c97621
Repository: `<repo>` (work only inside it; all paths below are relative to it)

## Goal
A job whose job.json or result.json holds a malformed `status` (not one of the known status strings) never crashes `agy-mc status`, `agy-mc status <id>`, `wait`, or `prune`, and is never written back into job.json.

## Context
- `antigravity_mission_control/jobstore.py` `refresh_job` (around line 127):
  - line 128 `if job.get("status") not in {"starting", "running", "canceling"}` raises TypeError when status is unhashable (e.g. a list);
  - line 138 `job["status"] = result.get("status", "error")` copies whatever result.json says (a list, a number, an unknown string) into job.json; if result.json is not an object, `.get` raises AttributeError.
  `list_jobs` catches only OSError, JSONDecodeError, KeyError, RuntimeError, so one bad entry crashes `agy-mc status`.
- Known statuses are the keys of `JOB_EXIT_CODES` (jobstore.py). A worker's result.json is normally written atomically by `write_terminal_result` or the worker, so malformed files mean corruption or manual edits: handle them safely, without crashing.
- Reproductions (both crash today with `TypeError: unhashable type: 'list'`):
  1. job.json `{"job_id":"stale-job","status":"running","pid":999999,"finished_at":"2020-01-01T00:00:00+00:00"}` with result.json `{"status":["done"]}`; run `AGY_MC_JOB_ROOT=<tmp> python3 -m antigravity_mission_control.cli prune --older-than 1d` and `... status`.
  2. job.json with `"status": ["done"]` directly.
- prune (jobs.py) already skips a non-string status read from job.json before refresh, and has an allowlist `PRUNABLE_STATUSES`. Its re-check under the lock calls `_prune_reason` on a fresh read, which can still see a malformed status.
- Tests are `unittest.TestCase`; CI runs `python -m unittest discover -s tests -v` without pytest. Suite: 91 tests. Storage is redirected with `mock.patch.object(jobstore, "JOB_ROOT", Path(tmp))`.

## Scope
- May modify: antigravity_mission_control/jobstore.py, antigravity_mission_control/jobs.py, tests/test_malformed_status.py (new), CHANGELOG.md
- Must not touch: everything else

## Steps
1. jobstore.refresh_job: compare status only when it is a string; a job whose status is not a string is returned unchanged (callers decide how to show it). When resolving from result.json, accept the result's status only if it is a string in `JOB_EXIT_CODES` and not starting/running/canceling; a result.json that is not an object, or has any other status, resolves the job to "crashed" (same as today's unreadable result.json).
2. list_jobs: an entry that still cannot be refreshed must be skipped like other unreadable entries, not crash the listing.
3. jobs.py `_prune_reason`: a non-string status returns "unknown status" (covers the re-check under the lock).
4. tests/test_malformed_status.py: both reproductions above for `status` (list form and single id) and `prune` (dry run and --yes; a valid old job next to the bad one is still removed); job.json is not rewritten with a malformed status; a stale running job with an unknown-string result status resolves to crashed.
5. CHANGELOG.md, under `## Unreleased`: one `Fix:` line in the file's style.

## Acceptance
- [ ] no crash on either reproduction for status, status <id>, prune
- [ ] malformed statuses are never written into job.json
- Verification commands: `python3 -m unittest tests.test_malformed_status -v`, `python3 -m unittest discover -s tests`, `python3 -m compileall -q antigravity_mission_control scripts tests`

## Skills
none

## Rework (round 2)
Your previous round's changes are still uncommitted in the working tree; build on them, do not start over. The orchestrator confirmed these findings. Fix every one of them:
- a-F2 [major] jobs.py cmd_cancel — `agy-mc cancel <id>` on a job.json whose status is `["done"]` raises `TypeError: unhashable type: 'list'` (it does `job.get("status") not in {...}` and `JOB_EXIT_CODES.get(...)`). → Guard it the same way as status/wait (non-string status is not cancelable: report it like any other finished job, exit code via `_exit_code`). Add a test.
- a-F1=b-F1 [minor] jobstore.refresh_job — a result.json object with no `status` resolves to `error` because of `result.get("status", "error")`. → Missing status resolves to `crashed`, like any other non-known status. Add a test.
- b-F3 [minor] jobs.py and jobstore.py — the unfinished-status set is defined twice (jobstore `UNFINISHED`, jobs `UNFINISHED_STATUSES`). → Keep one definition in jobstore and import it.
Scope is unchanged. Keep all existing tests passing.
