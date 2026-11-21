# 附录：v1.3.0 源码索引、实测数据、术语与核验命令

## 锁定快照

| 字段 | 值 |
|---|---|
| 上游仓库 | `Donchitos/Claude-Code-Game-Studios` |
| 版本 | `v1.3.0`（"Make me a game"） |
| 固定提交 | `abc0de79d6ceb0b5d7aa693945849b3937afbe6a` |
| 上游发布日期 | `2026-11-09` |
| 开源许可 | MIT |
| 本书采集日期 | `2026-11-21` |

## 逐章源码入口

| 章 | 主要对照文件 |
|---|---|
| 前言 | `README.md`、`CHANGELOG.md`、`UPGRADING.md`、`project.yaml` |
| 01 需求 | `CLAUDE.md`、`docs/COLLABORATIVE-DESIGN-PRINCIPLE.md`、`.claude/docs/coding-standards.md`、`.claude/rules/*.md` |
| 02 架构 | `.claude/settings.json`、`.claude/docs/directory-structure.md`、`.claude/hooks/validate-read.sh`、`.worktreeinclude` |
| 03 入门 | `.claude/skills/prototype/SKILL.md` 及 `references/one-shot-*.md`、`.claude/skills/start/SKILL.md`、`.claude/skills/next-step/SKILL.md`、`.claude/skills/cut/SKILL.md`、`.claude/scripts/project-state.sh` |
| 04 配置 | `.claude/hooks/yaml-helper.sh`、`.claude/skills/project-settings/SKILL.md`、`.claude/docs/config-resolution.md`、`.claude/docs/effects-map.md`、`project.yaml` |
| 05 角色 | `.claude/agents/*.md`、`.claude/docs/coordination-rules.md`、`.claude/docs/model-tiers.md` |
| 06 技能协议 | `.claude/skills/dev-story/SKILL.md`、`.claude/skills/help/SKILL.md`、`.claude/docs/automation-modes.md`、`.claude/docs/director-gates.md` |
| 07 产物 | `.claude/docs/templates/game-brief.md`、`.claude/docs/templates/story.md`、`docs/architecture/tr-registry.yaml`、`design/registry/entities.yaml`、`docs/architecture/control-manifest.md` |
| 08 实施 | `.claude/skills/dev-story/SKILL.md`、`.claude/scripts/story-facts.sh`、`.claude/scripts/one-shot-grow.sh`、`.claude/docs/run-and-observe.md` |
| 09 验收 | `.claude/skills/story-done/SKILL.md`、`.claude/scripts/review-receipts.sh`、`.claude/docs/error-recovery-protocol.md` |
| 10 Hook | `.claude/settings.json`、`.claude/hooks/*.sh`、`.claude/scripts/hook-input.sh`、`.claude/scripts/write-guard.sh`、`.claude/scripts/read-guard.sh` |
| 11 注册表 | `.claude/scripts/registry.sh`、三份注册表 YAML |
| 12 协作 | `.claude/skills/team-combat/SKILL.md`、`.claude/docs/coordination-rules.md`、`.claude/docs/error-recovery-protocol.md` |
| 13 引擎与品类 | `.claude/engines/engines.tsv`、`.claude/engines/README.md`、`.claude/scripts/engine-row.awk`、`.claude/docs/code-root-resolution.md`、`docs/engine-reference/web/VERSION.md`、`.claude/genres/chipsets.yaml` 及 `chipsets/*.md` |
| 14 上下文 | `.claude/docs/context-management.md`、`.claude/docs/templates/session-state.md`、`.claude/scripts/session-state.sh`、`.claude/scripts/rotate-session-state.sh` |
| 15 安全 | `SECURITY.md`、`.claude/settings.json`、`.claude/skills/security-audit/SKILL.md` |
| 16 验证与演进 | `studio-tests/README.md`、`studio-tests/catalog.yaml`、`.claude/scripts/skill-lint.sh`、`.claude/rules/skill-authoring.md`、`UPGRADING.md` |
| 17 最小实验 | `examples/mini_studio.py`、`examples/test_mini_studio.py` |

## v1.3.0 实测资产盘点

以下数字直接统计自 commit `abc0de79d6ceb0b5d7aa693945849b3937afbe6a`：

```text
.claude/agents/*.md            49
  model: inherit               30
  model: sonnet                16
  model: opus                   3
  model: haiku                  0
.claude/skills/*/SKILL.md      78   (75 个正式技能 + 3 个旧名转发层 help/settings/changelog)
.claude/rules/*.md             14
.claude/hooks/*.sh             18
  settings.json 注册命令       15   (另 3 个为 yaml-helper.sh / update-check.sh / log-instructions.sh)
.claude/scripts/*              49   (含 .sh / .awk / .js 辅助脚本)
.claude/docs/templates/*       74   (含 62 份主模板 + 指导文档与 one-shot-lean 起步文件)
.claude/genres/*               73   (chipsets.yaml + 品类卡片 + mashups/art-direction/online-and-devices/sources)
.claude/engines/engines.tsv    有   (Godot / Unity / Unreal / Web 四引擎统一表)
studio-tests/                  有   (catalog.yaml + quality-rubric.md + 75 技能与 49 角色行为规格)
settings.json permissions:
  allow                        31   (含 v1.3.0 新增 28 条只读脚本与 yaml-helper 只读函数)
  deny                        131   (Bash / PowerShell / Read / Edit 高危规则)
```

三个高频改名对照（v1.2.0 → v1.3.0）：
- `/help` → `/next-step`
- `/settings` → `/project-settings`
- `/changelog` → `/write-changelog`

## 核心术语速查

- **One-shot（单次可玩原型）**：v1.3.0 的默认主干道。通过 `/prototype` 问一轮最多约 8 个品类问题、生成一页 `design/game-brief.md`、在 `prototypes/<name>/` 搓出双击能玩的浏览器游戏并经无头浏览器冒烟后交接。
- **Studio Mode（工作室模式）**：v1.3.0 对原有重型工程体系的统称——49 个角色、每系统一份 GDD、ADR、史诗/冲刺计划、阶段门禁与 9 条 `/team-*` 流水线（对应 `modes.rigor` 的 `standard` / `full`）。
- **Chipset（品类卡片）**：`.claude/genres/chipsets/` 下的单品类知识卡，给 `/prototype` 提供分岔问题、手感变体、第一分钟默认要素和敌人种类底线。
- **Grow（成长为工程）**：在原型拿到 `PROCEED` 后，通过 `one-shot-grow.sh` 分五步提交将其拷出并重构成根目录的 Vite + TypeScript + Vitest + Playwright 工程，原原型目录保持不动。
- **Same-seed run（同种子回放）**：Grow 工程专享的回归锁。用同一颗随机种子和同一串输入脚本在改动前后回放游戏并对比状态行与截图，出现 `match no` 时强制停下来请人类裁决。
- **Own calls（AI 自主拍板清单）**：v1.3.0 `/dev-story` 收集、`/story-done` 逐条追认的清单——列出设计与故事没写明、由程序员自己拍板的数值、时机、颜色、边界行为或界面文案，由人类选“保留（写入故事）”或“修改（直接 `BLOCKED`）”。
- **Agent / Skill / Hook / Rule**：分别指 `.claude/agents/` 里的角色人设、`.claude/skills/` 里的斜杠剧本、`.claude/hooks/` 里挂在事件上的脚本、`.claude/rules/` 里按路径触发的编码规范。
- **`rigor` / `workflow` / `qa.level` / `review_mode` / `team.size`**：`rigor` 是总档位入口，自动展开后面 6 个子开关（含 `docs.density` 和 `story_granularity`）；其中任何显式写入的值都会压过展开。
- **Receipt（内容哈希回执）**：`review-receipts.sh` 打在 `stamp.txt` 里的文件内容哈希，用来戳穿“截完图又改过代码”的过期证据。
- **`NOT ASSESSED`（无法评估）**：四态判决里排在 `COMPLETE` 之上、`BLOCKED` 之下的状态，专防把“没测过 / 缺输入”混成通过。

## 自己动手核验路线

想在本机亲手复核本书的每一项数据与机制，按下面顺序敲一遍：

1. 检出固定提交并复核资产数：

```bash
git clone https://github.com/Donchitos/Claude-Code-Game-Studios.git
cd Claude-Code-Game-Studios
git checkout abc0de79d6ceb0b5d7aa693945849b3937afbe6a
find .claude/agents -name '*.md' | wc -l        # 49
find .claude/skills -name SKILL.md | wc -l      # 78 (75 + 3 shims)
find .claude/rules -name '*.md' | wc -l         # 14
find .claude/hooks -name '*.sh' | wc -l         # 18 (15 registered)
find .claude/genres -type f | wc -l             # 73
cat .claude/engines/engines.tsv
```

2. 实跑配置解析与项目状态：

```bash
bash .claude/hooks/yaml-helper.sh resolve_config
bash .claude/hooks/yaml-helper.sh resolve_setting modes.workflow
bash .claude/scripts/project-state.sh
bash .claude/scripts/registry.sh validate
```

3. 实跑技能静态检查与内容哈希回执：

```bash
bash .claude/scripts/skill-lint.sh dev-story
bash .claude/scripts/skill-lint.sh all | tail -n 3

f=$(mktemp); echo a > "$f"
bash .claude/scripts/review-receipts.sh hash "$f" > "$f.stamp"
bash .claude/scripts/review-receipts.sh check "$f.stamp"
echo b >> "$f"
bash .claude/scripts/review-receipts.sh check "$f.stamp"
rm -f "$f" "$f.stamp"
```

4. 跑本书配套的最小教学模型与 17 个单元测试：

```bash
cd examples
python3 -m unittest -v test_mini_studio.py
python3 mini_studio.py demo
```

## 许可与声明

上游 CCGS 采用 MIT 许可，其仓库、文档与脚本版权归原作者 Donchitos 及贡献者所有。本书为独立源码分析与重编作品，非上游官方文档；正文与实验代码同样采用 MIT 许可，文中引用上游文件名、脚本与版本记录均用于技术解读与核验。
