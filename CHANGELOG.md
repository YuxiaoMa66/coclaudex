# Changelog

## 1.2.0 — 2026-09-23
- Installable as a Claude Code plugin (`.claude-plugin/`); the skill moved to `skills/colaudex/`. Agent names may carry the `colaudex:` prefix.
- Combo and tier are chosen in two steps; tier options show only the models the chosen combo uses (`codex_run.py describe`). Execution and review tiers can differ.
- Plans must use the project's own test runner (a reviewer passed pytest tests that a unittest-only CI would never run).
- Sandbox-blocked pre-existing tests are PARTIAL, not a reason to widen access.
- `examples/agy-mission-control`: a full public audit trail of a three-slice run. Project page and README show it; social card `docs/assets/og.png`.

## 1.1.0 — 2026-09-23
From the fault-injection simulation (sandbox/sim1: BLOCKED, rework, orchestrator crash) and the paper run (sandbox/paper1: planted bib error).
- Metrics: Claude runs also write `.result.json`; new `codex_run.py stats` table (tier calibration data).
- Resume: rules for a dead EXECUTING/REVIEWING run (INFRA_FAIL, `--resume` from the jsonl thread id, keep the tree) and for CONFIRMING with the commit already made.
- Aborted attempts (BLOCKED/crashed) keep the round; outputs renamed `.blocked.*` / `.crashed.*`.
- Commit first, then set ACCEPTED.
- Rework handoff tells the executor that the previous round's changes are in the working tree.
- Input fixes (bib, plan data) are the orchestrator's; commit them separately and move `base_sha`.
- Paper review: reviewers get WebSearch/WebFetch; must report `Citations verified online: k/n`; Codex paper review forces `web_search="live"`.
- `test` tier stays cheap for paper slices (overrides `paper_exec`).

## 1.0.0 — 2026-09-23
First versioned release: plan → execute → review → confirm loop, combos A–D, tiers light/standard/heavy/test, Codex runner with watchdog and review-JSON validation, 5 Claude subagents.
