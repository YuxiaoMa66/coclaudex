# PLAN — antigravity-mission-control: job housekeeping (coclaudex public example)

Repo: YuxiaoMa66/antigravity-mission-control @ v0.5.0 (branch coclaudex-demo in a local clone). Baseline: `python3 -m pytest -q` → 64 passed.

## Requirements
1. Duration strings ("100s", "5m", "1h") are parsed in one shared place.
2. `agy-mc status` without a job id can be narrowed: newest N jobs, and/or by state.
3. `agy-mc prune` removes old finished job directories safely. It must never remove a job that is starting, running or canceling, and must only delete inside the job root.
Done = all three shipped with tests, full suite green, `--help` text for untouched commands unchanged.

## Slices
### 01-parse-duration (code, combo C, standard)
Extract the duration parsing in `cmd_wait` into `common.parse_duration`; `wait` keeps identical behavior and error messages. Scope: common.py, jobs.py, tests/test_duration.py (new).

### 02-status-filter (code, combo C, standard) — deps: none
`status [--limit N] [--state S ...]` for the list form; default output unchanged. Scope: cli.py, jobs.py, tests/test_status_filter.py (new).

### 03-prune (code, combo B; user chose Claude opus medium to execute, one Codex sol medium reviewer) — deps: 01
`prune --older-than DURATION [--yes]`: dry run by default; deletes only terminal jobs whose finished_at is older than the cutoff; JSON report of removed / kept / skipped. Risky (deletes data) → heavy: Claude opus executes, two Codex reviewers.
Scope: jobstore.py, jobs.py, cli.py, tests/test_prune.py (new).

### 04-docs-and-hardening (code+docs, combo B, standard) — deps: 01, 02, 03
Make the branch mergeable under CONTRIBUTING.md: document `status --limit/--state` and `prune` in every paired doc, allowlist the statuses prune treats as finished, add an Unreleased CHANGELOG entry, run npm test and npm pack --dry-run.

### 05-malformed-status (code, combo B, heavy) — deps: 04
Root-cause fix found in 04's review: jobstore.refresh_job trusts result.json's status and crashes on non-string statuses, which breaks `status` and `prune`. Validate in the shared code.

### 06-read-job-guard (code, combo C, light) — deps: 05
Root cause of 05's escalation: every command reads job.json through `jobstore.read_job`; reject a non-string status there so continue, cancel, worker finish and launch all fail with a clean error instead of a TypeError.
