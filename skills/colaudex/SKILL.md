---
name: colaudex
description: Claude + Codex plan→execute→review→confirm pipeline. Claude (this session) writes the requirements and plan and does the final confirmation. For each slice the user picks A/B/C/D, meaning who executes and who reviews (Claude or Codex), plus a tier (light/standard/heavy/overkill). For complex code builds and paper writing. Use when the user says colaudex, asks for Claude and Codex to split execution and review, wants cross-model execution and review, or wants a planned multi-slice build with an independent reviewer.
---

# colaudex

You (this session's model) are the **orchestrator**. You write the plan, dispatch executors and reviewers, confirm results, and commit. You do not execute slices yourself. Executors and reviewers never see this conversation; everything they need goes into files.

Skill dir (below: `$SK`): the base directory shown when this skill loads. That is `~/.claude/skills/colaudex` for a symlink install, or a folder in the plugin cache for a plugin install. Codex runner: `python3 $SK/scripts/codex_run.py`.

## 0. Setup (once per project)

1. The project must be a git repo with a clean working tree. If it is not a repo, offer to run `git init`. If the tree is dirty, ask the user whether to commit or stash first. Never discard their work.
2. Create `.colab/` with the subdirectories `tasks/ runs/ reviews/ confirm/`. Add `.colab/` to `.git/info/exclude`, not to `.gitignore`.
3. If any slice may use Codex, run `codex_run.py preflight`. If it fails, show the `detail` and offer to run every slice with Claude only.
4. Claude executors and reviewers are the subagents `colaudex-*` shipped in this repo's `agents/`, which set model and effort in frontmatter. Installed as a plugin, their type names carry the plugin prefix: use `colaudex:<claude.agent>` when the bare name from config is not in your agent list. New or edited agent files can take a few minutes to load. If Agent says "Agent type not found", wait briefly and retry, or start a new session. Meanwhile, use `general-purpose` with the config's `model`, prepend the agent file's body to the prompt, and note that effort falls back to the session default.
5. Handoffs and review prompts must carry the repo's **absolute path** (`{{REPO}}`), because Claude subagents do not start in the project directory.
6. If `.colab/STATE.md` already exists, **resume**: read `PLAN.md` and `STATE.md`, run preflight again if Codex slices remain, and continue each slice from its recorded state. Two states need care:
   - **EXECUTING or REVIEWING with no `.result.json` for the current round**: first check that nothing is still running (`pgrep -f "<slice>.r<N>"`). If a run is still alive, wait for it. If it is dead, treat it as an INFRA_FAIL. Set its outputs aside as an aborted attempt (see 2.3). For a Codex executor, read the `thread_id` from the `thread.started` event in the `.jsonl` and retry once with `--resume <thread_id>`; that works in any round. Keep the half-edited working tree; never reset it.
   - **CONFIRMING**: if `git log` already has the `colaudex(<slice>)` commit, just set ACCEPTED.

## 1. Plan

Write `.colab/PLAN.md`:
- **Requirements**, and a project-level definition of done.
- **Slices**, numbered `01-name`, `02-name`, and so on. Each slice needs: kind (`code` or `paper`), goal, scope (the files it may modify), steps, acceptance (checkable criteria plus verification commands), dependencies, and the Codex skills to use (or none).

Aim for each slice to be about half an hour of focused work, verifiable on its own, with a tight file scope. For a bug that is a pattern (a missing check, an unsafe call), grep every place the pattern occurs before writing the handoff, and put the fix at the shared entry point they all go through. Listing call sites one by one leads to rework round after round. Before writing acceptance commands, check how the project itself runs its checks (CI config, CONTRIBUTING, Makefile) and use the same runner and test style. Say it in the handoff's Context, so an executor does not write pytest tests for a project whose CI runs unittest. Paper work must live in git as Markdown or LaTeX, split into one file per section, so it can be diffed.

Show the plan and **wait for the user to approve it** before executing anything.

## 2. Per-slice loop

`STATE.md` holds a single table with one row per slice:
`| slice | kind | combo | tier | state | round | base_sha | codex_thread | note |`
Write the new state to `STATE.md` **before** every transition.
States: `PLANNED → EXECUTING → REVIEWING → CONFIRMING → ACCEPTED`, plus `REWORK`, `BLOCKED`, `ESCALATED`, and `INFRA_FAIL`.

### 2.1 Choose combo and tier

Unless a sticky choice from earlier still applies, ask in **two steps**, because the tier options depend on the combo. Write the questions in the user's language, and name the slice by what it does in plain words ("add a `prune` command that deletes old job folders"), not only by its id.

**Step 1: combo**. Use one AskUserQuestion with two questions:
- **Who does the work?** Labels spell out both roles, for example `C: Codex writes → Claude reviews`. Each description is one line on when this combo fits. Put your recommendation first, marked "(Recommended)". Recommend a cross-model combo: C when the handoff fully specifies the work, B when the slice needs judgment or deep context from the codebase. A and D are same-family: they are cheaper on one side, but the reviewer is less independent.
- **Apply to**: this slice only / all remaining slices in this phase.

**Step 2: tier**. Run `python3 $SK/scripts/codex_run.py describe --combo <X> --kind <kind>`. Then ask one AskUserQuestion whose four options are light, standard, heavy and overkill. `test` is not offered; use it only when the user asks for a cheap dry run. Each description shows **only the models this combo uses**, taken from that output, plus a few words on cost and depth. For example, for combo C: `standard: Codex gpt-6-luna (high) writes, Claude opus (medium) reviews. The default.` Never list the other backend's models. Mark standard as recommended unless the slice is risky (auth, deleting or migrating data, the core argument of a paper); then recommend heavy and say why in the question.

**overkill** runs the strongest models on both sides (Codex gpt-6-astra, Claude Fable) with two reviewers. Never recommend it by default; offer it for the few slices where a miss is very expensive, or when the user asks. Claude Fable needs usage credits on top of a plan, so say "uses Fable (extra usage credits)" in its option. If a Fable agent fails with a credits or access message, stop and ask whether to fall back to heavy's Claude models (opus) or to move that role to Codex; never switch silently.

Execution and review tiers may differ. If the user picks a mix, for example "opus writes, sol reviews" (heavy exec with standard review), record the tier as `exec:heavy/review:standard`, and pass each side its own tier: `--tier heavy` for the executor and `--tier standard` for the reviewer, or the matching Claude agent and model from that tier's config. A heavy second reviewer comes only with a heavy review tier.

The tier maps to models through `$SK/config.json`. Paper slices on light or standard execute with `paper_exec` (sol / opus); heavy already uses those models, overkill uses its own stronger ones, and test stays cheap. Only when the user asks for a cheap test run, use the `test` tier (Codex luna low, Claude haiku).

### 2.2 Handoff

1. Record `base_sha=$(git rev-parse HEAD)` in STATE.
2. Fill `$SK/templates/handoff.md` → `.colab/tasks/<slice>.md`. It must be self-contained: the executor sees nothing else.

### 2.3 Execute (state EXECUTING)

- **Codex**: run this with Bash, `run_in_background: true`:
  `python3 $SK/scripts/codex_run.py exec --tier <tier> --kind <kind> --prompt .colab/tasks/<slice>.md --out .colab/runs/<slice>.r<N> --cwd <repo>`
  (For round ≥2, or a retry after a crash, add `--resume <codex_thread>` when the same Codex model executes.) The worker rules are prepended automatically. Save `thread_id` from the result into STATE.
- **Claude**: write `$SK/templates/worker-rules.md` followed by the handoff to `.colab/tasks/<slice>.prompt.full.md`, then call Agent with `subagent_type` = the `claude.agent` from config and `model` = the `claude.model` from config, `run_in_background: true`, and a short prompt telling it to read that file in full and follow it as its instructions. Save its final message to `.colab/runs/<slice>.r<N>.last.txt`. When it completes, also write `.colab/runs/<slice>.r<N>.result.json` as `{"role":"exec","backend":"claude","tier":…,"model":…,"seconds":<duration_ms/1000>,"tokens":<subagent_tokens>,"status":…}` from the completion's usage block, so `stats` covers Claude runs too.

Wait for the completion notification. Do not poll.

**Aborted attempts** (BLOCKED, crashed, or INFRA_FAIL before a retry): before re-running the same round, rename that round's outputs from `<slice>.r<N>.*` to `<slice>.r<N>.blocked.*` or `.crashed.*`. For a Claude run, write its `.result.json` first. An aborted attempt does not use up a round; only REWORK increments `round`.

### 2.4 Check the execution result

- Codex `error_class: INFRA_FAIL`: retry once. If it fails again, set INFRA_FAIL and ask the user: wait and retry, or switch this role to Claude at the same tier.
- `STATUS: BLOCKED`: set BLOCKED and bring the reason back to the plan. Fix the plan or the handoff with the user; do not retry blindly. The re-run is an aborted attempt (see 2.3), in the same round.
- `sandbox_denied: true`: ask the user whether to widen access. Never widen it silently. Exception: if the executor's own work is verified and only pre-existing tests failed because the sandbox blocked them (for example `ps` or signals: "Operation not permitted"), do not widen anything. Treat it as PARTIAL and rerun the full suite yourself at confirmation.
- `STATUS: PARTIAL` or `UNKNOWN`: still go to review, and note it.
- **Scope check (always)**: compare `git diff --name-only <base_sha>` plus untracked files against "May modify". Any file outside the scope is a blocker for confirmation. Build and cache artifacts from test runs, such as `__pycache__/` or `.pytest_cache/`, are not violations. Add them to `.git/info/exclude` so they stop showing up.
- Reviewer `sandbox_denied: true` is expected: a read-only reviewer often can't run tests. It is not an error.
- Also check that the executor made no commits: `git log <base_sha>..HEAD` must be empty.
- `.colab/` is git-excluded but still on disk. A project check that walks the file tree (link checkers, linters, doc tests) can trip over it. If a failure points into `.colab/`, move that file aside, rerun, and treat it as noise, not a finding. Raw model output is saved as `.txt` for this reason.

### 2.5 Review (state REVIEWING)

1. Fill `$SK/templates/review-code.md` or `review-paper.md` (handoff path, base_sha, focus) → `.colab/reviews/<slice>.r<N>.prompt.md`.
2. Run the reviewer:
- **Codex**: run `python3 $SK/scripts/codex_run.py review --tier <tier> --kind <kind> --prompt <that prompt> --out .colab/reviews/<slice>.r<N> --cwd <repo>`. The review lands in `…r<N>.json`. If `INVALID_REVIEW` or `INFRA_FAIL`, retry once, then fall back to a Claude reviewer at the same tier.
- **Claude**: call Agent with `subagent_type` = the `claude.agent` from config and `model` = the `claude.model` from config. The prompt is the filled review prompt plus: "Write the JSON to `.colab/reviews/<slice>.r<N>.json`, then run `python3 $SK/scripts/codex_run.py validate <that file>` and fix it until valid." It is a fresh agent. Never give it the executor's transcript. When it completes, write `…r<N>.result.json` the same way as for a Claude executor, with `"role":"review"` and `"status"` = the verdict.
- **Heavy tier**: run a second reviewer with the same backend, in parallel, with a different focus. Code: "correctness and edge cases" vs "design, scope and maintainability". Paper: "argument and evidence" vs "citations and consistency". Use the output paths `…r<N>a` / `…r<N>b`.

### 2.6 Confirm (state CONFIRMING). This is your job; never delegate it.

For every finding, write `.colab/confirm/<slice>.r<N>.md` with this line format:
`F1 [major] VALID|INVALID — reason`
With two reviewers (heavy, overkill), prefix ids with the reviewer, `a-F1` and `b-F1`, and mark findings both raised as `a-F2=b-F1`, so the Finish report can show how many VALID findings each reviewer added. That number decides whether the second reviewer is worth its cost.
- A finding whose evidence you cannot reproduce is INVALID. Check the cited line or passage yourself.
- **Code**: run the verification commands yourself. Never trust the executor's or reviewer's claim that tests pass.
- **Paper**: open every blocker or major finding's quoted passage. Spot-check the new citations yourself. Any fabricated citation is a VALID blocker.
- Add your own findings if you see problems the reviewer missed.
- **Paper**: a paper review whose summary does not start with `Citations verified online: k/n` (with k = n, or the rest reported as unverified) is not a citation check. Re-run it rather than trusting a pass.
- **Input fixes**: a VALID finding in material outside the executor's scope (plan data, a bibliography, fixtures) is yours to fix. Commit it separately, then set STATE's `base_sha` to the new HEAD, so the next review diff shows only the executor's work.

Decision:
- **No VALID blocker or major finding** → commit, **then** set ACCEPTED. Stage only the files in scope: `git add -- <scope files>`, then commit with the message `colaudex(<slice>): <goal>`, following the session's commit-attribution instructions. Put leftover minor findings into STATE's note column.
- **VALID blocker or major finding and round < max_rounds (2)** → **REWORK**. Put the VALID findings into the handoff's Rework section, then `round += 1`. Ask the user whether to keep the same executor or move up one tier (give your recommendation). Go to 2.3.
- **round ≥ max_rounds, or verdict `reject` with VALID blockers** → **ESCALATED**. Summarize for the user and ask them to decide: re-plan the slice, accept as-is, take over manually, or drop it.

## 3. Finish

When every slice is ACCEPTED (or the user has decided on the escalated ones), run the project-level verification. Report per slice: combo, tier, rounds, and final verdict. For heavy or overkill slices, report VALID findings per reviewer (a only, b only, both). Also give where the time or rework went: run `python3 $SK/scripts/codex_run.py stats` and include its table. (These rows are the data for recalibrating the tier defaults later.) Do not delete `.colab/`; it is the audit trail.

## Rules

- Run slices **sequentially** in the main working tree. (Deliberate limit: no parallel slices or worktrees yet. Add them once Codex rate limits for long tasks are measured, capped at 2 concurrent Codex executors.)
- Only the orchestrator commits. Never push unless the user asks.
- Never pass a model to Codex outside config's `allowed_models`. Never use `chatgpt-web/*` models.
- Do not edit `~/.codex/config.toml`. All overrides go through `codex_run.py` flags.
- Global Codex hooks or AGENTS.md style rules (for example a "write minimal code" rule) can make executors skip running tests. The worker rules override them, and you re-run the tests at confirmation anyway.
