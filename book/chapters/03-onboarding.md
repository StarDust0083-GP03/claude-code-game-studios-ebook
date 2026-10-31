# 第 03 章 入门：`/start` 如何把空白仓库变成项目

## 场景

克隆完仓库，你面对一个空项目：没有引擎，没有设计文档，只有一个模板和一堆规则。此刻最合理的动作不是随便挑一个技能，而是让仓库先看清自己处于什么状态，再决定路线。这就是 `/start` 的职责。

在固定快照上直接运行它依赖的状态脚本，输出如下（实测，`bash .claude/scripts/project-state.sh`）：

```
root	/tmp/claude-game-studios-source	-
engine	-	unset
code_root	src	detected
source_files	0	src
concept	-	absent
systems_index	-	absent
gdd_files	0	design/gdd/*.md
adr	0	docs/architecture/adr-*.md
story	0	production/epics/**/story-*.md
prototype	0	prototypes/*/
sprint	0	production/sprints/*.md
milestone	0	production/milestones/*.md
origin_url	https://github.com/Donchitos/Claude-Code-Game-Studios.git	.git/config
stage_yaml	-	project.yaml
stage_txt	-	absent
stage	-	unset
phase	-	unset
phase_inferred	concept	nothing
```

这张表是 `/start` 的全部输入。每行三列：字段名、值、来源。第三列比第二列更重要，它告诉模型这个值是配置里写的、目录里推出来的，还是根本没找到。

## 状态判定

`/start` 的正文把这张表映射成判断：

- `engine` 为空且 `concept` 缺失，说明这是未配置的新项目。
- `source_files` 为 `unknown` 时要明确说"代码根无法解析"，绝不能说"没有代码"。这两句话的后续动作完全不同。
- `origin_url` 含 `donchitos/claude-code-game-studios` 时，说明你的 `origin` 还指向模板仓库，直接 push 会把提交送到上游模板。脚本会建议改名 `template` 再添加自己的远程。
- `phase_inferred` 只是按文件数量猜的，正文明确要求忽略它。一个只有代码、没有设计文档的项目不是 Production 阶段。

最后一条很值得注意。仓库自己提供了一个猜测字段，又在流程里禁止使用它。原因是猜测会把"代码很多"误判成"进入生产"，从而跳过设计和架构阶段。作者宁愿让你手动判定，也不愿让一个看似聪明的推断替代事实。

## 四条路径

`/start` 第二个问题只问一件事：你现在处于哪一步。

- A，完全没有想法。
- B，模糊的念头，比如"想做个太空题材"。
- C，清晰概念，知道类型和核心玩法，但没写下来。
- D，已有作品：设计文档、原型、代码或计划。

选完之后，它只给出一个"下一步"，不给完整路线。理由是路线长度取决于 rigor，而 rigor 还没确定。选 D 时会先报告扫描结果，比如"代码根下有 N 个源文件，N 份设计文档，引擎未设置"，再决定从 `/project-stage-detect` 还是 `/setup-engine` 开始。

如果回答与扫描结果冲突，正文要求指出一次并重新问。比如你选了 A"没有想法"，但磁盘上有代码，它会说"我在 `src/` 发现了代码，你是不是想选 D"。

## 强度推断

第四个阶段是确定 rigor。规则是一张三行的信号表：

| 你的描述里出现 | 推荐 rigor |
|---|---|
| 开放世界、RPG、模拟、沙盒、派系、制作、经济、MMO、多人、很多系统 | full |
| 发布、商业、Steam、一个清晰的核心循环 | standard |
| Game Jam、周末、原型、第一个游戏、小、只是试试 | minimal |
| 以上都没有，或还没想法 | minimal（默认） |

推断结果会以卡片形式展示，并说明理由用的是你的原话。卡片上还会写明后果：minimal 大约四步到代码，standard 大约八份设计文档，full 在 standard 基础上加验证构建和全量证据。

关键在于：`/start` 不会问你"要不要 rigor"，它只问"是否保存"。rigor 的调整入口统一在 `/settings`。这个设计避免了六个相关设置被逐个询问，也避免了用户在没有上下文时凭空选一个抽象档位。

## 写入与不写入

`/start` 只写三项：`project.stage`（以及旧版镜像 `production/stage.txt`）、`modes.rigor`、`modes.automation`。写入必须经过显式确认，并且通过 `set-stage.sh` 和 `config-set.sh` 两个辅助脚本完成。

它明确不写 `modes.review_mode`，也不写另外五个被 rigor 前置的设置。原因写在 `project.yaml` 的注释里：一旦某个键被显式写入，rigor 展开就再也改不动它，用户之后调用 `/settings` 调档位会失效。

这是一个容易犯的错误。很多人会想"我先把默认值都写进配置文件，清楚一点"。在这套系统里，这样做等于把档位锁死。

## 交接而不是代跑

最后一个阶段只有一行输出：`Type /setup-engine to begin.`

正文特别要求：不要替用户启动那个技能，即使用户刚说了"好，开始吧"。用户必须自己输入命令。这个细节看起来吹毛求疵，实际是权限设计的一部分。用户亲手输入命令，意味着他知道接下来会发生什么；模型代为调用，则把一个需要确认的动作变成了自动连锁。

## 常见误解

误解一：`/start` 会自动创建完整的项目骨架。它只写三个设置，然后交接。真正的引擎配置在 `/setup-engine`，设计在 `/brainstorm`。

误解二：`code_root: src` 说明引擎是 Godot。这里 `src` 只是"目录里恰好只有一个候选根"的推断结果，来源列写的是 `detected`，不是 `engine.name`。

误解三：rigor 推断是随意的。它有一张信号表，而且推断结果会在卡片上给出理由，用户可以当场否决。

## 练习

1. 在你自己的项目副本上运行 `project-state.sh`，找出三处"来源是推断而不是配置"的字段。
2. 假设你选了路径 C（清晰概念）并输入"一个关于送信的叙事小游戏"，按信号表推断 rigor，并说明理由。
3. 如果 `/start` 把 `modes.rigor` 写进 `project.yaml`，之后你手动把 `modes.workflow` 也写进去，会发生什么？

## 答案提示

1. 常见的是 `code_root`（来源 `detected`）、`phase_inferred`（来源 `nothing` 或文件计数）、`gate_level` 的默认部分。任何来源列不是 `project.yaml` 或 `project.local.yaml` 的值都属于推断或默认。
2. 叙事、小游戏、没有出现商业发布或大型系统信号，落在 minimal 或 standard 边界。按表，"一个清晰的核心循环"倾向 standard，但"小"倾向 minimal，卡片应展示推断并给出理由，由用户确认。
3. `modes.workflow` 被显式钉住，rigor 展开不再改变它。之后调 rigor 只影响其余五个设置，workflow 保持你写的值。这是 `project.yaml` 注释里警告的行为。
