Reviewer (codex gpt-6-sol medium): fix, F1 major. Tests could not run in its read-only sandbox (expected).
Orchestrator: scope 9 files OK; unittest 90 OK; npm test 13/13; npm pack OK; sync_skill_bundle leaves no diff; read CHANGELOG and REFERENCE.zh-CN diffs: accurate and in the files' voice.
F1 [major] VALID — reproduced: job.json with `"status": ["done"]` makes `prune --older-than 1d` crash with `TypeError: unhashable type: 'list'` (raised in jobstore.refresh_job), so one bad entry stops the whole cleanup and no report is printed.
  Also found: plain `agy-mc status` crashes on the same entry (list_jobs does not catch TypeError). Pre-existing since v0.5.0 and in jobstore.py, outside this slice's scope → follow-up, noted in the PR.
O1 [nit] VALID, own — CHANGELOG names the internal `common.parse_duration`; the user-facing effect is that `wait --timeout` also accepts `d`.
Decision: REWORK round 2 (F1, O1), same executor (user chose Claude sonnet medium).
