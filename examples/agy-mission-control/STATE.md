| slice | kind | combo | tier | state | round | base_sha | codex_thread | note |
|---|---|---|---|---|---|---|---|---|
| 01-parse-duration | code | C | standard | ACCEPTED | 2 | 0fc10c83c62def2c077de308e1aef71447230390 | 01a0cebd-d560-7141-a4b7-ed6986663e8d | r1 tests were pytest-only (CI runs unittest); nit: raise from None |
| 02-status-filter | code | C | standard | ACCEPTED | 1 | 843b73c696bcea76918740251ef1aca357665311 | 01a0cec7-393f-7013-9211-136255fd6c01 | nit: filter/job_id check in main() |
| 03-prune | code | B | exec:heavy(opus) review:standard(sol) | ACCEPTED | 2 | 89ca34dd9a18d6afebb4065d8245f50710c56b9e | | follow-ups: same-user symlink races (minor), allowlist terminal statuses |
| 04-docs-and-hardening | code | B | standard | ACCEPTED | 2 | ee8e1246fce2b0e58edae1411ada8e81caf035ad | | escalated: malformed result.json status (root cause in refresh_job) → slice 05 |
| 05-malformed-status | code | B | heavy | ACCEPTED | 2 | af605979a53abc0dd5cc78b35784eb8c92c97621 | | escalated: continue etc. still crash → slice 06 (guard in read_job) |
| 06-read-job-guard | code | C | light | ACCEPTED | 1 | 0d4a8a280ffb3e8334eeb5f85f88ef6f7253d261 | 01a0cf2b-846f-7c02-80fd-cc41953c9704 | 2 nits |
