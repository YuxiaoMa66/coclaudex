# Example: six slices on a real repository, merged as a pull request

The target is [antigravity-mission-control](https://github.com/YuxiaoMa66/antigravity-mission-control) v0.5.0, a Python CLI with 64 tests. The goal was job housekeeping. The run started from commit `0fc10c8`, and the result is [pull request #2](https://github.com/YuxiaoMa66/antigravity-mission-control/pull/2).

This folder is the audit trail as colaudex left it. Only local paths were replaced with `<repo>` and `<tmp>`.

| slice | who | tier | rounds | result |
|---|---|---|---|---|
| 01 shared `parse_duration` | Codex writes, Claude reviews | standard | 2 | accepted |
| 02 `status --limit / --state` | Codex writes, Claude reviews | standard | 1 | accepted |
| 03 `prune --older-than` (deletes data) | Claude writes, Codex reviews | opus writes, sol reviews | 2 | accepted, follow-ups noted |
| 04 paired docs, status allowlist | Claude writes, Codex reviews | standard | 2 | escalated → accepted, root cause moved to 05 |
| 05 malformed statuses | Claude writes, two Codex reviewers | heavy | 2 | escalated → accepted, root cause moved to 06 |
| 06 guard in `read_job` | Codex writes, Claude reviews | light | 1 | accepted |

The user picked the combo and tier for every slice from 02 onward.

End state: 103 tests pass, up from 64 (39 new). CI's bundle-sync, compile, `npm test` and `npm pack` checks pass locally. Agent time came to about 36 minutes across 20 runs.

## What happened

**Too lenient (01).**
- The reviewer rated pytest-style tests as a style nit and passed them.
- CI runs `python -m unittest discover` without pytest installed. The new module would fail to import there. On a machine with pytest installed, the 14 new tests would silently never run.
- Confirmation caught it. The handoff was partly to blame, because it said "run with pytest". See [`confirm/01-parse-duration.r1.md`](confirm/01-parse-duration.r1.md).

**A miss (03).** Neither reviewer noticed that the new delete command treated `cancel_failed` jobs as finished, although their worker may still be alive. The orchestrator did.

**Too strict (03).** In round 2, a Codex reviewer rated symlink races inside a private 0700 directory as blockers. Checked against the threat model, they were downgraded to minor, and the reasons are on file in [`confirm/03-prune.r2.md`](confirm/03-prune.r2.md).

**Two escalations, one root cause (04 → 05 → 06).**
- In 04, the review found that a malformed `status` in a job file crashed prune. Reproducing it showed that plain `agy-mc status` crashed too, which was a bug already in v0.5.0.
- The 05 handoff listed call sites to guard. Each round, another site turned up: `cancel`, then `continue`, the worker and launch.
- Both slices hit the two-round limit with a valid major finding still open, so colaudex stopped and asked the user each time.
- The fix that ended it was one check in `read_job`, which every command already goes through (06, one round).
- That lesson is now a skill rule: grep every occurrence of a bug pattern first, and fix it at the shared entry point.

**Two reviewers, counted (05).**
- Heavy runs two reviewers with different focus. They agreed on one finding (a result without a status became `error` instead of `crashed`).
- Only reviewer a, focused on correctness, found the `cancel` crash, which was the one valid major finding.
- Only reviewer b, focused on design, found two minor issues.
- See [`confirm/05-malformed-status.r1.md`](confirm/05-malformed-status.r1.md).

**colaudex's own bug (06).**
- The target repo has a test that checks every Markdown link on disk. It flagged links inside colaudex's raw run output in `.colab/runs/*.last.md`.
- colaudex now saves raw output as `.txt`, and the skill says to treat a check that trips over `.colab/` as noise, not as a finding.

## Files

- [`PLAN.md`](PLAN.md), [`STATE.md`](STATE.md): the plan and the final state table
- [`tasks/`](tasks): the handoffs the executors received, with their Rework sections
- [`reviews/`](reviews): reviewer JSON as returned (`05-…r1a` and `r1b` are the two heavy reviewers)
- [`confirm/`](confirm): the orchestrator's VALID/INVALID decision on every finding
- [`patches/`](patches): the six commits (`git am` applies them on top of `0fc10c8`)
- [`stats.tsv`](stats.tsv): time and tokens per run (`codex_run.py stats`)

Codex executors report `PARTIAL` in this repo because their sandbox cannot start `ps`, which three existing lifecycle tests need. The orchestrator reran the full suite outside the sandbox every time.
