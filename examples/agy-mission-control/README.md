# Example: three slices on a real repository

The target is [antigravity-mission-control](https://github.com/YuxiaoMa66/antigravity-mission-control) v0.5.0, a Python CLI with 64 tests. The goal was job housekeeping. The run started from commit `0fc10c8` and worked on a local branch. Nothing was pushed to that repository.

This folder is the audit trail as colaudex left it. Only local paths were replaced with `<repo>`.

| slice | who | tier | rounds | result |
|---|---|---|---|---|
| 01 shared `parse_duration` | Codex writes, Claude reviews | standard | 2 | accepted |
| 02 `status --limit / --state` | Codex writes, Claude reviews | standard | 1 | accepted |
| 03 `prune --older-than` (deletes data) | Claude writes, Codex reviews | opus writes, sol reviews | 2 | accepted, 3 follow-ups |

End state: 89 tests pass. That is the original 64 plus 25 new ones. CI's skill-bundle and compile checks also pass locally.

## What happened

**Slice 01: the reviewer passed tests that CI would never run.**
- Codex wrote the new tests with pytest. The Claude reviewer rated that a style nit and passed the slice.
- During confirmation, the orchestrator read `.github/workflows/ci.yml`. CI runs `python -m unittest discover` on a clean Python without pytest.
- In CI, the new module would fail to import. On a machine with pytest installed, `unittest` silently ran 64 tests and skipped all 14 new ones.
- The handoff shared the blame: it had said "run with pytest". Both were fixed, and round 2 passed. See [`confirm/01-parse-duration.r1.md`](confirm/01-parse-duration.r1.md).

**Slice 02** passed on the first try. The orchestrator reran the full suite, the CI sync check and the CLI error paths before committing.

**Slice 03: a deletion command, reviewed by the other model.**
- In round 1, the Codex reviewer found a symlink-swap path that could create a lock file outside the job root.
- The orchestrator added a finding the reviewer missed. A job in `cancel_failed` counted as finished, although its worker process may still be alive.
- Round 2 fixed both. It checks for live PIDs, takes the lock through an `O_NOFOLLOW` directory fd, and renames each directory, then verifies it, before deleting it.
- Codex then raised two more races and one hardening point, rating them blocker/major. The orchestrator checked each one against the threat model: the job root is a private 0700 directory, and existing commands already walk it the same way. It downgraded all three to minor, with reasons, and kept them as follow-ups rather than burn a third round. See [`confirm/03-prune.r2.md`](confirm/03-prune.r2.md).

Both directions of disagreement happened in the same run. Once a reviewer was too lenient, and once too strict. In both cases, confirmation reproduced the claim before acting on it.

## Files

- [`PLAN.md`](PLAN.md), [`STATE.md`](STATE.md): the plan and the final state table
- [`tasks/`](tasks): the handoffs executors received, including the Rework sections
- [`reviews/`](reviews): reviewer JSON as returned
- [`confirm/`](confirm): the orchestrator's VALID/INVALID decision on every finding
- [`patches/`](patches): the three commits (`git am` applies them on top of `0fc10c8`)
- [`stats.tsv`](stats.tsv): time and tokens per run (`codex_run.py stats`)

Executor and reviewer time for all three slices came to about 14 minutes. Codex executors report `PARTIAL` here, because their sandbox cannot start `ps`, which three existing lifecycle tests need. The orchestrator reran the full suite outside the sandbox each time.
