# Slice 04-docs-and-hardening: document the new commands and allowlist finished statuses

Kind: code · Round: 2 · Base commit: ee8e1246fce2b0e58edae1411ada8e81caf035ad
Repository: `<repo>` (work only inside it; all paths below are relative to it)

## Goal
The branch meets CONTRIBUTING.md: `status --limit/--state` and `prune` are documented in every paired doc, prune only deletes jobs whose status is on an explicit allowlist of finished statuses, and CHANGELOG has an Unreleased entry.

## Context
- Slices 01–03 (already committed) added `common.parse_duration` (ms/s/m/h/d), `agy-mc status [--limit N] [--state S ...]`, and `agy-mc prune --older-than DURATION [--yes]` (dry run unless --yes; keeps unfinished jobs, jobs with a live pid/launcher_pid, and jobs without a parseable finished_at; never follows symlinks; JSON report with removed / would_remove / skipped). Read `agy-mc status --help`, `agy-mc prune --help` (`python3 -m antigravity_mission_control.cli ...`) and the code in antigravity_mission_control/jobs.py for exact behaviour. Document only what the code does.
- CONTRIBUTING.md: docs are maintained in pairs (README.md / README.zh-CN.md, docs/REFERENCE.md / docs/REFERENCE.zh-CN.md). After changing `references/`, run `python3 scripts/sync_skill_bundle.py` and include the synchronized bundle.
- Where the commands are documented today: README.md and README.zh-CN.md (command list around `agy-mc status [job-id]` / `agy-mc wait`), docs/REFERENCE.md and docs/REFERENCE.zh-CN.md (`## Command map` table, `## Job states and exit codes`), references/job-lifecycle.md.
- Match the existing voice of each file: terse, factual, no marketing words. The Chinese files are written Chinese, not word-for-word translation; follow their existing terms.
- Review found that prune treats *any* status other than starting/running/canceling as finished. Known statuses are the keys of `JOB_EXIT_CODES` in jobstore.py.
- Tests are `unittest.TestCase`; CI runs `python -m unittest discover -s tests -v` without pytest. Suite now: 89 tests. npm: 13 tests.

## Scope
- May modify: README.md, README.zh-CN.md, docs/REFERENCE.md, docs/REFERENCE.zh-CN.md, references/job-lifecycle.md, antigravity_mission_control/skill_bundle/** (only through `scripts/sync_skill_bundle.py`), CHANGELOG.md, antigravity_mission_control/jobs.py, tests/test_prune.py
- Must not touch: everything else (no version bump, no release notes under docs/releases)

## Steps
1. jobs.py: prune deletes only jobs whose status is in an explicit set: done, done_with_warnings, error, crashed, cancel_failed, canceled. Any other status (including unknown or missing) is skipped with reason "unknown status". Keep every existing guard (live pid, finished_at, symlinks, re-check under lock).
2. tests/test_prune.py: an old job with status "queued" (unknown) and one with no status are kept with that reason.
3. Docs: add `status --limit/--state` and `prune` to the README pair, the REFERENCE pair (command map row, plus a short note on what prune keeps and that it is a dry run without --yes), and references/job-lifecycle.md. Then run the sync script.
4. CHANGELOG.md: a `## Unreleased` section above 0.5.0 listing the three additions and the parse_duration `d` unit, in the file's existing style.

## Acceptance
- [ ] allowlist in place, with the new tests
- [ ] every paired doc updated on both sides; bundle synchronized (`python3 scripts/sync_skill_bundle.py && git diff --exit-code -- antigravity_mission_control/skill_bundle` shows no further change after your commit-ready state)
- Verification commands: `python3 -m unittest discover -s tests -v`, `python3 -m compileall -q antigravity_mission_control scripts tests`, `npm test`, `npm pack --dry-run`, `python3 scripts/sync_skill_bundle.py` then `git status --short`

## Skills
none

## Rework (round 2)
Your previous round's changes are still uncommitted in the working tree; build on them, do not start over. The orchestrator confirmed these findings. Fix every one of them:
- F1 [major] jobs.py cmd_prune selection — a job.json whose `status` is not a string (e.g. `["done"]`) crashes prune with `TypeError: unhashable type: 'list'` inside `refresh_job`, so no report is printed. → In prune, check `isinstance(job.get("status"), str)` right after reading job.json and before `refresh_job`; skip with reason "unknown status" otherwise. Also treat a non-dict job.json as unreadable. Do not change jobstore.py (the same crash in `status` is a separate follow-up). Add a test with `"status": ["done"]` next to a valid old job: prune must not crash, must skip the bad one, and must still remove the valid one with --yes.
- O1 [nit] CHANGELOG.md — the parse_duration line names an internal function. → Say what users see: `wait --timeout` also accepts `d` (days).
