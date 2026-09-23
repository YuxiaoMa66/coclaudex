# colaudex

Claude Code skill: Claude plans and confirms; Claude or Codex executes and reviews each slice (combos A/B/C/D, tiers light/standard/heavy).

- `skill/` — the skill (SKILL.md, config, Codex runner, templates, review schema)
- `agents/` — Claude executor/reviewer subagents (model + effort in frontmatter)
- `sandbox/` — throwaway test projects, git-ignored

## Install (symlinks, so edits here are live)

```bash
ln -s "$PWD/skill" ~/.claude/skills/colaudex
for f in agents/colaudex-*.md; do ln -s "$PWD/$f" ~/.claude/agents/; done
```
