# Slice {{SLICE_ID}}: {{TITLE}}

Kind: {{code|paper}} · Round: {{N}} · Base commit: {{BASE_SHA}}
Repository: `{{REPO}}` (work only inside it; all paths below are relative to it)

## Goal
{{One sentence: what is true when this slice is done.}}

## Context
{{Only what this slice needs: relevant file paths, decisions already made, and interfaces it must respect. The executor cannot see the conversation.}}

## Scope
- May modify: {{explicit file list, or globs}}
- Must not touch: {{files and areas that are off-limits}}

## Steps
1. {{from PLAN.md}}

## Acceptance
- [ ] {{a checkable criterion}}
- Verification commands: `{{e.g. pytest tests/test_auth.py -q}}`
- For paper slices: {{the questions this section must answer; the sources it may cite}}

## Skills
{{Name the skills to use, e.g. $latex. Otherwise write: none}}

## Rework (round {{N}} only; delete this section in round 1)
Your previous round's changes are still uncommitted in the working tree; build on them, do not start over. The orchestrator confirmed these findings. Fix every one of them:
- {{F1 [major] location — problem → required change}}
