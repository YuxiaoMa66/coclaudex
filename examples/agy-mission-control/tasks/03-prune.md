# Slice 03-prune: `agy-mc prune` for old finished jobs

Kind: code · Round: 2 · Base commit: 89ca34dd9a18d6afebb4065d8245f50710c56b9e
Repository: `<repo>` (work only inside it; all paths below are relative to it)

## Goal
`agy-mc prune --older-than DURATION [--yes]` reports, and with `--yes` deletes, job directories of finished jobs whose `finished_at` is older than DURATION. It can never delete an unfinished job or anything outside the job root.

## Context
- Job storage: `antigravity_mission_control/jobstore.py`. `JOB_ROOT` holds one directory per job (`JOB_ROOT/<job_id>/job.json`, plus result, spec, `job.lock`). `validate_job_id`, `job_dir`, `read_job`, `refresh_job`, `job_lock` (flock on `<job dir>/job.lock`, not reentrant) live there. `refresh_job` resolves dead starting/running/canceling jobs to a terminal status.
- Statuses: see `JOB_EXIT_CODES`. Unfinished = starting, running, canceling, **or any job whose `pid` or `launcher_pid` is still alive** (`jobstore.pid_alive`). `cancel_failed` in particular means the worker could not be stopped and may still be running.
- `finished_at` is written by `common.utc_now()` = `datetime.now(timezone.utc).isoformat()`.
- Durations: `common.parse_duration(text) -> float` seconds (ms/s/m/h/d), raises ValueError. Added in slice 01.
- CLI: `antigravity_mission_control/cli.py` `build_parser` and `main`; command handlers live in jobs.py (`cmd_status`, `cmd_wait`, ...). Look at how `status` validates arguments (slice 02) and match it.
- Tests are `unittest.TestCase` classes. CI runs `python -m unittest discover -s tests -v` with **no pytest installed**; do not import pytest. Tests redirect storage with `mock.patch.object(jobstore, "JOB_ROOT", Path(tmp))` (see tests/test_job_state.py). Existing suite: 74 tests.

## Scope
- May modify: antigravity_mission_control/jobstore.py, antigravity_mission_control/jobs.py, antigravity_mission_control/cli.py, tests/test_prune.py (new)
- Must not touch: everything else

## Steps
1. Parser: `prune --older-than DURATION` (required) and `--yes`. An invalid or non-positive duration is a usage error.
2. Selection, for each entry directly under JOB_ROOT:
   - skip (and report) anything that is not a real directory (symlinks included), whose name fails `validate_job_id`, or whose job.json is missing, unreadable, or has a `job_id` different from the directory name;
   - refresh the job; skip unfinished jobs; skip jobs without a parseable `finished_at`;
   - candidates are finished jobs with `finished_at` older than now minus the duration.
3. Without `--yes`: dry run, delete nothing. With `--yes`: for each candidate, take `job_lock`, re-read the job and re-check it is still finished and old enough, then remove that one directory. Never follow symlinks while deleting.
4. Print one JSON document: `{"dry_run": bool, "older_than_seconds": float, "removed": [...], "would_remove": [...], "skipped": [{"job_id" or "entry": ..., "reason": ...}]}` (removed is empty on a dry run, would_remove empty with --yes). Exit 0.
5. tests/test_prune.py: dry run deletes nothing; --yes deletes only old finished jobs; running/starting/canceling jobs are never deleted however old; recent finished jobs kept; missing finished_at kept; mismatched job_id kept; a symlink in JOB_ROOT pointing at a directory outside it is neither followed nor deleted, and its target survives; invalid duration is a usage error.

## Acceptance
- [ ] all the behaviour above, each covered by a test
- [ ] no deletion path outside JOB_ROOT, no symlink following
- Verification commands: `python3 -m unittest tests.test_prune -v` and `python3 -m unittest discover -s tests` (count must include the new tests)

## Skills
none

## Rework (round 2)
Your previous round's changes are still uncommitted in the working tree; build on them, do not start over. The orchestrator confirmed these findings. Fix every one of them:
- O1 [major] jobs.py `_prune_reason` — a `cancel_failed` job (set in cmd_cancel when terminate_process_group fails) counts as finished although its worker may still be alive. → Treat a job as unfinished whenever `pid_alive(job.get("pid"))` or `pid_alive(job.get("launcher_pid"))`, whatever its status; check it at selection and again under the lock. Add a test: an old `cancel_failed` job whose pid is the test process (`os.getpid()`) is kept.
- F2 [major] jobs.py cmd_prune `with job_lock(name)` — if the entry is replaced by a symlink after selection, `job_lock` opens `JOB_ROOT/name/job.lock` with O_CREAT through the link and creates a file outside JOB_ROOT. → In prune, never open anything through a path that could be a symlink: open the job directory with `os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW` (relative to an fd for JOB_ROOT is fine) and take the flock on `job.lock` opened with `dir_fd=` that fd. Add a test that swaps a candidate for a symlink to an outside directory right before deletion (e.g. by patching a hook or `_real_job_dir`) and asserts nothing was created or removed outside.
- F1 [minor, fix anyway] jobs.py `shutil.rmtree(root / name)` — the directory could be replaced between the re-check and rmtree. → Rename-then-verify: `os.rename(JOB_ROOT/name, JOB_ROOT/f".prune-{name}-{uuid}")` (rename never follows a symlink), then check with lstat that the renamed entry is a real directory whose job.json has the same job_id; only then rmtree it. If a check fails, rename it back and skip with a reason. Leftover `.prune-*` entries are reported as skipped by later runs (they fail validate_job_id).
Keep every existing prune test passing.
