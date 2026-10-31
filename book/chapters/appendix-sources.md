# 附录：源码索引、术语与核验路线

## 快照

| 字段 | 值 |
|---|---|
| 仓库 | Donchitos/Claude-Code-Game-Studios |
| 提交 | 05ad7c8a5b8aa2aa86bbd3439ae7cf7295cac418 |
| 日期 | 2026-10-19 |
| 框架版本 | 1.2.0 |
| 许可 | MIT |
| 本书采集日期 | 2026-10-31 |

## 每章源码入口

| 章 | 主要文件 |
|---|---|
| 前言 | `README.md`、`LICENSE`、`project.yaml` |
| 01 需求 | `CLAUDE.md`、`docs/COLLABORATIVE-DESIGN-PRINCIPLE.md`、`.claude/docs/coding-standards.md`、`.claude/rules/*.md` |
| 02 架构 | `.claude/settings.json`、`.claude/docs/directory-structure.md`、`.claude/docs/context-management.md` |
| 03 入门 | `.claude/skills/start/SKILL.md`、`.claude/scripts/project-state.sh` |
| 04 配置 | `.claude/docs/config-resolution.md`、`.claude/hooks/yaml-helper.sh`、`.claude/docs/settings-guidance.md` |
| 05 角色 | `.claude/agents/*.md`、`.claude/docs/agent-roster.md`、`.claude/docs/model-tiers.md`、`.claude/docs/coordination-rules.md` |
| 06 技能协议 | `.claude/skills/dev-story/SKILL.md`、`.claude/docs/automation-modes.md`、`.claude/rules/skill-authoring.md` |
| 07 产物 | `.claude/docs/templates/story.md`、`docs/architecture/tr-registry.yaml`、`design/registry/entities.yaml`、`.claude/docs/director-gates.md` |
| 08 实施 | `.claude/skills/dev-story/SKILL.md`、`.claude/docs/code-root-resolution.md`、`.claude/docs/run-and-observe.md` |
| 09 验收 | `.claude/skills/story-done/SKILL.md`、`.claude/scripts/review-receipts.sh`、`.claude/docs/error-recovery-protocol.md` |
| 10 Hook | `.claude/settings.json`、`.claude/hooks/*.sh`、`.claude/scripts/write-guard.sh`、`.claude/scripts/read-guard.sh` |
| 11 注册表 | `.claude/scripts/registry.sh`、三份注册表 YAML |
| 12 协作 | `.claude/skills/team-combat/SKILL.md`、`.claude/docs/coordination-rules.md`、`.claude/docs/error-recovery-protocol.md` |
| 13 引擎 | `.claude/docs/code-root-resolution.md`、`docs/engine-reference/**`、`.claude/docs/technical-preferences.md` |
| 14 上下文 | `.claude/docs/context-management.md`、`.claude/docs/templates/session-state.md`、`.claude/scripts/session-state.sh` |
| 15 安全 | `SECURITY.md`、`.claude/settings.json`、`.claude/skills/security-audit/SKILL.md` |
| 16 验证 | `studio-tests/README.md`、`studio-tests/catalog.yaml`、`.claude/scripts/skill-lint.sh`、`.claude/skills/skill-test/SKILL.md` |
| 17 实验 | `examples/mini_studio.py`、`examples/test_mini_studio.py` |

## 实测数据

以下数字来自快照的实际统计和脚本运行，不是文档转述。

```
.claude/agents/*.md        49
  model inherit            30
  model sonnet             16
  model opus                3
.claude/skills/*/SKILL.md  74
.claude/rules/*.md         14
.claude/hooks/*.sh         18
  registered commands      15
.claude/docs/templates/*   71
```

`skill-lint.sh all` 的最后一行是 `checked 74 of 74`。

`project-state.sh` 在未配置的快照上报告：`engine unset`、`code_root src detected`、`source_files 0`、`gdd_files 0`、`adr 0`、`stage unset`、`phase_inferred concept`。

`resolve_config` 的默认输出：rigor minimal，workflow minimal，qa.level minimal，review_mode solo，team.size individual，automation collaborative。

`registry.sh validate`：三份注册表各 0 条目，五个检查项全为 0。

## 术语

Agent（角色）：`.claude/agents/` 下的 Markdown 文件，定义职责、工具、模型、回合上限。派生成子代理后运行。

Skill（技能）：`.claude/skills/<name>/SKILL.md`，斜杠命令的正文，包含前置元数据、注入命令和分阶段流程。

Hook：`.claude/hooks/` 下的脚本，由 `settings.json` 注册到事件上，读标准输入 JSON，用退出码影响行为。

Rule（规则）：`.claude/rules/` 下按路径生效的编码标准，编辑匹配路径时加载。

rigor：一个前置设置，展开成六个子设置。默认 minimal。

workflow：决定设计文档要写到多细，以及实施前必须存在哪些产物。

qa.level：决定需要什么测试证据，与 workflow 分开设置。

review_mode：full、lean、solo，决定总监评审门禁跑到什么程度。

team.size：individual、small、studio，决定团队流水线派生多少角色。

Story（故事）：最小执行单元，含验收标准、证据要求、文件范围、依赖。

ADR：架构决策记录，带状态和版本，故事引用其摘要。

TR-ID：需求编号，权威文本在 `docs/architecture/tr-registry.yaml`。

Receipt（回执）：内容哈希戳，用于判断证据是否比代码旧。

NOT ASSESSED：无法评估，排在通过之上、失败之下。

## 核验路线

想自己验证书中的结论，按这个顺序：

1. 克隆固定提交，统计文件数：

```bash
git clone https://github.com/Donchitos/Claude-Code-Game-Studios.git
cd Claude-Code-Game-Studios
git checkout 05ad7c8a5b8aa2aa86bbd3439ae7cf7295cac418
find .claude/agents -name '*.md' | wc -l
find .claude/skills -name SKILL.md | wc -l
```

2. 看配置解析：

```bash
bash .claude/hooks/yaml-helper.sh resolve_config
bash .claude/hooks/yaml-helper.sh resolve_setting modes.workflow
```

3. 看项目状态和注册表：

```bash
bash .claude/scripts/project-state.sh
bash .claude/scripts/registry.sh validate
```

4. 看技能结构：

```bash
bash .claude/scripts/skill-lint.sh dev-story
bash .claude/scripts/skill-lint.sh all | tail -1
```

5. 看证据回执：

```bash
f=$(mktemp); echo a > "$f"
bash .claude/scripts/review-receipts.sh hash "$f" > "$f.stamp"
bash .claude/scripts/review-receipts.sh check "$f.stamp"
echo b >> "$f"
bash .claude/scripts/review-receipts.sh check "$f.stamp"
```

6. 跑本书的实验：

```bash
cd examples
python3 -m unittest -v test_mini_studio.py
python3 mini_studio.py demo
```

7. 官方语义对照：Claude Code Hooks 文档（`https://code.claude.com/docs/en/hooks`）用于确认退出码和事件行为。Hook 语义会随版本变化，移植前以你当前版本的文档为准。

## 未覆盖的问题

本书没有回答这些问题，它们需要真实项目和真实计费：

- 一次完整游戏开发的实际 token 成本。
- standard 与 full 档位在真实项目上的质量差异。
- 多代理并行时的冲突率和返工率。
- 模型对这套长提示词的实际遵循率。
- 在 Unity 或 Unreal 项目上的端到端表现。

作者自己的对照实验只覆盖了四个小游戏和一次盲评，样本很小，书中引用时保留了它的原始结论和局限。

## 上游许可与本书声明

上游模板采用 MIT 许可。本书是独立撰写的静态研究，不是上游官方文档，也不代表作者观点。书中的批评、改进建议和实验代码由本书作者负责。阅读器样式与构建脚本参考了本地电子书项目，仅用于排版与检索。
