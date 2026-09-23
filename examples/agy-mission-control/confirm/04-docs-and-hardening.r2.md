Reviewer r2 (codex gpt-6-sol medium): fix, F1 major.
Orchestrator: unittest 91 OK; npm test 13/13; compileall OK; sync leaves no diff. r1 F1 and O1 fixed (non-string status skipped, non-dict job.json already rejected by read_job, CHANGELOG reworded).
F1 [major] VALID — reproduced: a stale `running` job (dead pid) whose result.json has `"status": ["done"]` crashes prune with TypeError in `_prune_reason`; `jobstore.refresh_job` also writes the list back into job.json, and plain `agy-mc status` crashes on it too. Root cause is refresh_job trusting result.json, in jobstore.py, outside this slice's scope.
Decision: round 2 of 2 with a VALID major → ESCALATED. User chose: accept 04 as is, fix the root cause in a new slice 05 (jobstore in scope), then open the PR.
