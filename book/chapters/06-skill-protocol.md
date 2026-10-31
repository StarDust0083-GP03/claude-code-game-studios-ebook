# 第 06 章 Skill 协议：一个命令从解析到交接

## 场景

你输入 `/dev-story production/epics/stealth/story-003.md`。屏幕上先出现一行配置解析结果，然后模型开始按 Phase 1 到 Phase 7 推进：找故事、检查前置条件、标记进行中、选择程序员、派活、检查结果、写总结。

这一章拆开这条命令的执行过程。理解它之后，你能自己写一个符合这套协议的技能，也能判断一个技能在什么情况下会失败。

## 文件结构与前置元数据

`.claude/skills/` 下有 74 个目录，每个目录一个 `SKILL.md`。以 `dev-story` 为例：

```yaml
---
name: dev-story
description: "Implements one story in code with tests, following its ADRs. ..."
argument-hint: "[story-path]"
user-invocable: true
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, Write, Edit, Agent, AskUserQuestion,
  Bash(bash "*/.claude/skills/dev-story/../../hooks/yaml-helper.sh" resolve_config *),
  Bash(bash .claude/scripts/story-facts.sh *), ...
model: sonnet
---
```

每个字段都有明确作用：

`name` 是命令名，也是模型通过 Skill 工具调用时用的标识。`description` 决定什么时候该用它，写得越具体，误触发的机会越小。`argument-hint` 告诉用户该带什么参数。`user-invocable: true` 表示可以手动输入 `/dev-story`。`disable-model-invocation: true` 表示模型不能自己启动它，必须由用户触发，这对会产生文件变更的技能很常见。

`allowed-tools` 是一份精确到子命令的授权清单。注意它授权的是特定 Bash 调用，而不是整个 Bash 工具。`Bash(bash .claude/scripts/story-facts.sh *)` 只允许跑这个脚本，不允许跑 `rm`。

`model: sonnet` 是该技能建议的模型档位，是否生效取决于启动方式，第 5 章已经解释。

## 正文的第一段是命令

几乎每个技能的正文开头都有一行被反引号包裹的 shell 命令，前面带 `!`：

```
!`bash "${CLAUDE_SKILL_DIR}/../../hooks/yaml-helper.sh" resolve_config --keys automation,workflow,qa.level,gate_level,engine_values,specialists,perf_budgets,system_overrides`
```

Claude Code 在加载技能时执行它，把标准输出直接插入提示词。紧接着一行：

> Resolved above — use as-is. No block → defaults in `.claude/docs/config-resolution.md`.

这两句合起来完成了一次"确定性注入"。模型不需要知道配置在哪、怎么解析、有哪些层级，它只需要读注入结果。与此同时，注入失败的情况也有兜底说明。

这个模式有一个前提：命令必须被精确授权。`allowed-tools` 里的那段长模式就是为此存在。授权写错，整次技能调用中止，而不是降级运行。仓库在 `config-resolution.md` 里说明了这个取舍：注入是严格的，权限提示是宽松的，两者不能混用。

## 七段式流程

`dev-story` 的正文是一张清单加七个阶段：

```
- [ ] Phase 1: story found, tier resolved
- [ ] Phase 2: prerequisites checked (ADR, manifest, dependencies)
- [ ] Phase 3: story marked In Progress (one ask)
- [ ] Phase 4: programmer and engine specialist chosen
- [ ] Phase 5: work handed out with a full brief
- [ ] Phase 6: finished? parse check, run and look, one Run result line
- [ ] Phase 7: summary, ## Files, checkpoint, closing block
```

清单的作用不只是给模型看，也是给用户看进度。每个阶段有明确的输入、输出和停止条件。

Phase 1 解析参数。没有参数时读会话检查点里的当前任务，确认后继续；没有故事时给出下一步命令，而不是猜一个。

Phase 2 做前置检查，按 workflow 档位分三列。full 档要求需求注册表存在，缺失就停止；standard 档只是可选；ADR 必须是 Accepted 状态；依赖故事必须是 Complete。任何一项不满足，就进入 Phase 7 写 BLOCKED 检查点，不派生程序员代理。

Phase 3 只问一次："我可以把故事标记为进行中吗？这会改故事状态、更新冲刺状态文件，并在结束时列出改动文件。"用户拒绝，就继续实施但不改状态，并在总结里写明"Story not marked In Progress — declined"。

Phase 4 用一张表选人：Foundation 层给引擎程序员，UI 类型给 UI 程序员，Visual/Feel 给玩法程序员，AI 给 AI 程序员，网络给网络程序员。配置故事不需要代理，直接改数据文件。

Phase 5 派活。这里有一条重要约束：简报要点名文件，不粘贴整份文档。故事文件、需求条目、ADR 摘要、控制清单的对应层规则、命名规范、性能预算、测试路径，逐项列出。明确告诉子代理"哪些输入在当前离线不存在，不要去找"。

Phase 6 检查结果。先看文件是否真的写出来了，再看测试是否存在，然后做解析检查，最后运行并观察。三个结果词被固定下来：`OBSERVED`、`NOT VERIFIED`、`N/A`。

Phase 7 输出固定格式的总结，更新故事的 `## Files`，写会话检查点，最后打印三行收尾：故事状态、运行结果、下一步。

![dev-story 的七个阶段：两道门禁与一个产物检查点](../../wiki/assets/diagrams/dev-story.svg)

## 提问协议

技能里反复出现同一段话：

> 用提问工具询问。没有提问工具时，把选项编号列出并结束回合等待。被跳过或关闭的问题不是回答，用纯文本再问一次。

这段话解决了一个真实故障：在无人值守或工具缺失的环境里，提问调用可能返回"全部跳过"。如果模型把跳过当成默认同意，就会在没有批准的情况下写文件。仓库的处理是明确区分"没回答"和"同意"，遇到前者就停下。

`automation-modes.md` 把这个规则扩展到三种自动化模式：collaborative 每次都问；guided 只问重大决策；autonomous 不问但要把决策写进日志。三种模式下，"被跳过的问题不是回答"都成立。

## 引用而不是内嵌

技能正文经常写"读 `.claude/docs/automation-modes.md`"或"见 `.claude/docs/director-gates.md`"，而不是把整份规范抄进来。

好处是单一事实来源，改一处所有技能同步。代价是模型可能不读，或者读了不照做。仓库用两种方式缓解：关键规则在技能里重述一两句，其余交给按需加载。

在 `director-gates.md` 里还有一条反向约束：技能派生总监做评审时，**不要自己读评审定义文件**，而是把文件路径放进子代理的提示词，让子代理在自己的上下文里读。理由是节省父会话的 token，同时保证评审者看到完整定义。

## 收尾契约

好的技能有明确的结束条件。`dev-story` 的最后一段规定：

```
Story: [path] — [Implemented | INCOMPLETE — <breakage> | BLOCKED — <reason>]
Run result: [OBSERVED — … | NOT VERIFIED — … | N/A — …]
Next step: [...]
```

状态词只有三种，每种对应不同下一步。`INCOMPLETE` 时下一步是继续实施，`BLOCKED` 时下一步是解除阻塞的具体动作。没有"基本完成"这种模糊状态。

`story-done` 有类似的四态判决：COMPLETE、COMPLETE WITH NOTES、NOT ASSESSED、BLOCKED，并规定了优先级顺序。第 9 章会拆解。

## 常见误解

误解一：技能是确定性的。它是一份给模型的步骤说明，模型可能跳步、合并步骤、或者误解某条规则。真正的确定性在脚本里。

误解二：`allowed-tools` 限制了技能能做什么。它只是免去权限提示，不构成沙箱；真正能拦住的是 `settings.json` 的 deny 列表和 Hook 的退出码。

误解三：技能越详细越好。`effects-map.md` 被反复提醒不要在运行时读，因为它太大。技能正文也有同样的问题，过长会挤占上下文并降低遵循率。

## 练习

1. 找两个技能，对比它们的 `allowed-tools`，说明为什么一个需要 `Agent` 而另一个不需要。
2. 阅读 `dev-story` 的 Phase 2，列出 full 档和 minimal 档各自的前置条件差异。
3. 为一个"生成变更日志"的技能设计前置元数据和收尾契约，要求它在没有 git 历史时明确报告而不是编造。

## 答案提示

1. 需要派生专家的技能（`dev-story`、`team-*`）需要 `Agent`；只做读写分析的技能（`code-review`、`design-review`）不需要。授权越窄，越不容易误用。
2. full 档要求需求注册表存在、ADR 必须 Accepted、控制清单缺失要警告；minimal 档不期待需求注册表，ADR 只在故事点名时检查。
3. `allowed-tools` 含 `Bash(git log *)`；收尾契约里明确 `NO_HISTORY` 状态和"未生成，因为仓库没有提交记录"的输出，禁止用推测填充。
