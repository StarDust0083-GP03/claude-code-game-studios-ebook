# Upstream snapshot

- Repository: https://github.com/Donchitos/Claude-Code-Game-Studios
- Commit: `05ad7c8a5b8aa2aa86bbd3439ae7cf7295cac418`
- Commit date: 2026-10-19
- Framework version: 1.2.0 (`project.yaml`)
- License: MIT
- Collected: 2026-10-31

## Counts measured on that commit

| Item | Count | How |
|---|---:|---|
| Agent files | 49 | `find .claude/agents -name '*.md' \| wc -l` |
| Agent model inherit | 30 | frontmatter `model:` |
| Agent model sonnet | 16 | frontmatter `model:` |
| Agent model opus | 3 | frontmatter `model:` |
| Skills | 74 | `find .claude/skills -name SKILL.md \| wc -l` |
| Rules | 14 | `find .claude/rules -name '*.md' \| wc -l` |
| Hook scripts | 18 | `find .claude/hooks -name '*.sh' \| wc -l` |
| Registered hook commands | 15 | commands in `.claude/settings.json` |
| Document templates | 71 | `find .claude/docs/templates -type f \| wc -l` |

Three hook scripts are not registered in `settings.json`: `yaml-helper.sh`
(a sourced library), `log-instructions.sh`, and `update-check.sh`. The README's
"15 hooks" badge refers to the registered commands; both numbers are correct
under their own definition.

## Scripts run against the snapshot

```bash
bash .claude/scripts/project-state.sh
bash .claude/hooks/yaml-helper.sh resolve_config
bash .claude/hooks/yaml-helper.sh resolve_config --keys rigor,workflow,qa.level,review_mode,team.size,gate_level
bash .claude/scripts/registry.sh validate
bash .claude/scripts/registry.sh next-id story stealth
bash .claude/scripts/skill-lint.sh dev-story
bash .claude/scripts/skill-lint.sh all | tail -1
bash .claude/scripts/review-receipts.sh hash <file>
bash .claude/scripts/review-receipts.sh check <stamp>
```

These commands only read the clone, except the receipt demo which writes into a
temporary directory.

## What was not tested

- A full game-development session with Claude Code.
- Token cost, model quality, or parallel-agent conflict rates.
- End-to-end behaviour on Unity or Unreal projects.
- The upstream framework's own test suite; the referenced `tests/` directory is
  not present in this clone.
