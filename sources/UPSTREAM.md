# Upstream snapshot

- Repository: https://github.com/Donchitos/Claude-Code-Game-Studios
- Commit: `abc0de79d6ceb0b5d7aa693945849b3937afbe6a`
- Commit / Release date: 2026-11-09
- Framework version: 1.3.0 (`project.yaml`, release "Make me a game")
- License: MIT
- Collected: 2026-11-21

## Counts measured on that commit

| Item | Count | How / Notes |
|---|---:|---|
| Agent files | 49 | `find .claude/agents -name '*.md' \| wc -l` |
| Agent model `inherit` | 30 | frontmatter `model:` |
| Agent model `sonnet` | 16 | frontmatter `model:` |
| Agent model `opus` | 3 | frontmatter `model:` |
| Agent model `haiku` | 0 | frontmatter `model:` |
| Skill `SKILL.md` files | 78 | `find .claude/skills -name SKILL.md \| wc -l` (75 active skills + 3 legacy shims: `help`, `settings`, `changelog`) |
| Path-scoped rules | 14 | `find .claude/rules -name '*.md' \| wc -l` |
| Hook scripts | 18 | `find .claude/hooks -name '*.sh' \| wc -l` |
| Registered hook commands | 15 | commands under `hooks` in `.claude/settings.json` |
| Helper scripts | 49 | files under `.claude/scripts/` (`.sh`, `.awk`, `.js`) |
| Document templates | 74 | `find .claude/docs/templates -type f \| wc -l` (62 main templates + guidance & `one-shot-lean/` starter files) |
| Genre knowledge files | 73 | files under `.claude/genres/` (`chipsets.yaml`, genre sheets, `mashups.md`, `art-direction.md`, `online-and-devices.md`, `sources.md`) |
| Unified engine table | 1 | `.claude/engines/engines.tsv` (Godot, Unity, Unreal, Web) |
| Framework spec suite | present | `studio-tests/` (`catalog.yaml` tracking 75 skills + 49 agents, `quality-rubric.md`, `skills/`, `agents/`, `templates/`) |

Three hook scripts are not registered in `.claude/settings.json`: `yaml-helper.sh`
(a sourced configuration library), `update-check.sh` (invoked by `session-start.sh`),
and `log-instructions.sh` (opt-in diagnostic). Both "15 hooks" (registered) and
"18 scripts" (files on disk) are accurate under their own definitions.

Similarly, `.claude/skills/` holds 78 `SKILL.md` files on disk because the three
renamed v1.2.0 commands (`/help` → `/next-step`, `/settings` → `/project-settings`,
`/changelog` → `/write-changelog`) remain as thin forwarding shims alongside the
75 active skills (including the new `/cut`).

## Verification commands for readers

```bash
git checkout abc0de79d6ceb0b5d7aa693945849b3937afbe6a
bash .claude/scripts/project-state.sh
bash .claude/hooks/yaml-helper.sh resolve_config
bash .claude/hooks/yaml-helper.sh resolve_config --keys rigor,workflow,qa.level,review_mode,team.size,gate_level
bash .claude/scripts/registry.sh validate
bash .claude/scripts/registry.sh next-id story stealth
bash .claude/scripts/skill-lint.sh dev-story
bash .claude/scripts/skill-lint.sh all | tail -1
bash .claude/scripts/review-receipts.sh hash <file>
bash .claude/scripts/review-receipts.sh check <stamp>
cat .claude/engines/engines.tsv
```

## What was not tested

- A full multi-week commercial game-development session with Claude Code.
- Live token billing, model adherence rates across providers, or parallel-agent merge conflict rates.
- End-to-end builds inside Unity or Unreal editors.
- Internal unit tests for `yaml-helper.sh` / hook shell parsers (those tests are not shipped in the public template repo; `studio-tests/` covers skill and agent static/spec/category reviews only).
