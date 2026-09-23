Reviewers (heavy, codex gpt-6-sol high x2): a = correctness and edge cases, b = design/scope/maintainability. Both: fix.
Orchestrator: unittest 100 OK; both original reproductions fixed through the CLI (stale job → crashed, no list written back, status lists both jobs).
a-F1=b-F1 [blocker→minor] VALID — result.json `{}` resolves to `error` (old default kept), handoff said any non-known status → crashed. Reproduced. Not a crash and `error` is a valid status, so not a blocker; fix anyway (one token).
a-F2 [major] VALID — `agy-mc cancel job2` on job.json status ["done"] → `TypeError: unhashable type: 'list'` (reproduced). Same class as the slice goal; must not ship.
b-F2 [major→minor] VALID — wait on malformed data: no result → `{"status":"ERROR","error":"Job job2 has no result yet"}`; non-object result → `"Job result must be an object"`. Clean error envelopes, no traceback. Left as is.
b-F3 [minor] VALID — unfinished-status set defined twice (jobstore UNFINISHED and jobs UNFINISHED_STATUSES). Fix: single definition.
Per reviewer: both 1 (a-F1=b-F1); a only 1 VALID major (a-F2); b only 2 VALID minor (b-F2, b-F3).
Decision: REWORK round 2 (a-F2, a-F1=b-F1, b-F3), same executor (user chose Claude opus medium).
