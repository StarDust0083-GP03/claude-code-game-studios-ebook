# 第 06 章 Skill 协议：一条斜杠命令怎么从解析走到交接

## 场景：敲下一行命令，后台到底发生了什么

你在终端里敲下一行：

```text
/dev-story production/epics/stealth/story-003.md
```

回车之后，你还没来得及看清，屏幕最前面就自动冒出了一段算得清清楚楚的配置块，接着 Claude 列出 7 个复选框阶段，从找故事、查前置条件、问你能不能标成 In Progress，一路推到派程序员写代码、查磁盘产物、跑解析检查、看截图，最后吐出三行格式工整的收尾块。

如果把一个技能目录拆开，它既不是二进制程序，也不是随便写的一段“请帮我写代码”的提示词，而是一套**带元数据、带确定性注入、带防压缩拆页、带收尾契约的轻量协议**。

## 78 个 `SKILL.md` 的真相：75 个正式技能 + 3 个旧名转发层

在 v1.3.0 里数 `.claude/skills/*/SKILL.md`，硬盘上实测是 **78 个**，但 README 写的是 **75 个技能**。这并不是统计出错，而是 v1.3.0 把三个容易和其他 AI 工具撞车的常用命令改了名：

- `/help` → **`/next-step`**
- `/settings` → **`/project-settings`**
- `/changelog` → **`/write-changelog`**

旧的 `help/`、`settings/`、`changelog/` 目录没删，而是改成了只有 20 来行的兼容转发层（shim）：你敲旧名时，它先老老实实打印一行 `/help is now /next-step. Running /next-step.`，然后调 `Skill` 工具把参数原样甩给新技能，自己什么活都不干。另外 v1.3.0 新增了收尾砍需求用的 `/cut`，凑齐了 75 个正式技能。

## 前置元数据：每一行都在管什么

拿 `.claude/skills/dev-story/SKILL.md` 的开头举个例子：

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

拆开看几个关键开关：
- **`description`**：Claude 靠这段话判断“用户随口说的话该不该触发这个技能”。写得越具体、把“什么时候不该用”也写明白，误触发就越少。
- **`disable-model-invocation: true`**：这行非常关键。像 `/dev-story`、`/story-done`、`/launch-checklist` 这类直接改文件或推进状态的技能，都加了这把锁——**模型自己绝不能擅自调用，必须由人亲手敲命令触发**。所以 v1.3.0 里 `/create-stories` 和 `/story-done` 专门修了一个旧毛病：不再把“现在开始 `/dev-story`”做成弹窗选项，而是直接把命令打印出来让你自己敲。
- **`allowed-tools`（精确到子命令）**：早年 34 个技能图省事，在 `allowed-tools` 里直接写了个光秃秃的 `Bash`，等于一进技能就预批准了所有 shell 命令。v1.2.0 之后全部收窄到了具体脚本和子命令，比如 `Bash(bash .claude/scripts/story-facts.sh *)` 只免弹窗放行这一个脚本。
- **v1.3.0 踩出的一个权限坑**：Claude Code 对技能自带的 `allowed-tools` **只在技能启动的那一轮生效**。只要技能中途停下来问你一个问题，等你回答完进入下一轮，它再调自己的只读脚本时又要弹窗求批准。为了治这个烦人的连环弹窗，v1.3.0 直接在 `.claude/settings.json` 的全局 `permissions.allow` 里一口气加了 28 条只读框架脚本和 `yaml-helper.sh` 7 个只读子命令的白名单；写文件和跑你项目代码的命令，依然留在技能自己手里或每次问你。另外 v1.3.0 还顺手修了 5 个原地改文件的技能（`/team-qa`、`/review-all-gdds`、`/write-changelog`、`/localize`、`/skill-test`）漏写 `Edit` 工具导致每次都被迫整文件重写或卡弹窗的 bug。

## 正文第一行的 `!`：把确定性计算从模型手里抢过来

几乎所有核心技能的正文一上来，不等废话，先顶一行反引号包住的感叹号命令：

```bash
!`bash "${CLAUDE_SKILL_DIR}/../../hooks/yaml-helper.sh" resolve_config --keys automation,workflow,qa.level,gate_level,engine_values,specialists,perf_budgets,system_overrides`
```

Claude Code 在把技能正文喂给模型**之前**，先执行这行 shell，把标准输出原样插进提示词里。下一行紧跟着交代：“上面已经算好了，直接照着用；要是没出现这个块，说明 shell 预处理没开，去读默认配置。”

这招彻底省掉了模型“自己找 `project.yaml` → 自己算 5 级优先级 → 自己展开 `rigor` → 算错还一脸自信”的整条翻车链。`/next-step` 甚至把 `.claude/scripts/story-status.sh` 也用 `!` 注入进正文，让模型一睁眼就看到按优先级排好序的未完成故事清单，不准它自己重新扫文件乱排序。

## 长技能为什么要拆 `references/`（防压缩丢步）

写复杂技能很容易踩一个隐蔽的坑：把七八百行步骤全塞进一个 `SKILL.md` 里。会话跑久了一旦触发上下文压缩（Compaction），Claude Code 重挂技能时**只会保留开头一部分**，后半截的验收、截图、收尾规则直接凭空蒸发。

所以 CCGS 把 14 个最长的技能（像 `/prototype`、`/dev-story`、`/story-done`、`/setup-engine`、`/gate-check`、`/design-system` 等）全部拆瘦了：**主 `SKILL.md` 只留配置注入、核心铁律、一张简短的阶段总览清单，每个具体阶段或冷门分支扔进同目录下的 `references/*.md`**，每个阶段标题下写死一句：“现在先读 `references/xxx.md` 再照着干；如果中途发生了上下文压缩，重新读一遍。”

以 `/dev-story` 的 7 段清单为例，它既是模型的执行路线图，也是给用户看的实时进度条：

```text
- [ ] Phase 1: story found, tier resolved
- [ ] Phase 2: prerequisites checked (ADR, manifest, dependencies)
- [ ] Phase 3: story marked In Progress (one ask)
- [ ] Phase 4: programmer and engine specialist chosen
- [ ] Phase 5: work handed out with a full brief
- [ ] Phase 6: finished? parse check, run and look, one Run result line; a grown game's same-seed run
- [ ] Phase 7: summary, ## Files, checkpoint, closing block
```

![dev-story 的七个阶段：两道门禁与一个产物检查点](../../wiki/assets/diagrams/dev-story.svg)

顺手一提，如果技能里需要派生总监子代理做评审（`director-gates.md`），规则还特意反着来了一手：**父技能自己不准读评审定义文档，只把文件路径塞进子代理的简报里让子代理自己读**。省了父会话的上下文，也保证评审者拿到完整原件。

## 提问协议：跳过绝不等于同意

翻遍所有交互型技能，你都会反复撞见同一段几乎一字不差的话：

> 用提问工具询问；没有提问工具就把选项编号列在消息最末尾，停下来等回复，问题后面别再追加建议。**被跳过、关闭或返回空答案的问题，绝对不算回答**：什么都不写、什么都不改，换纯文本重新问一遍。

这是针对真实翻车场景打的补丁。在无交互界面或者用户不小心按 Esc 关掉弹窗时，提问工具可能返回“跳过/空值”。如果模型自作聪明把“没反对”当成“默认同意”，就会在你没点头的情况下改掉故事状态甚至重写文件。

这条铁律在 `.claude/docs/automation-modes.md` 的三种自动化模式里全线生效：
- `collaborative`：关键步骤次次问；
- `guided`：小事自己定、大事（改范围、删文件、改配置结构）必须问；
- `autonomous`：一路自动跑并把每个决策写进 `decision-log.md`，但撞上 `automation_always_ask` 清单里的类别，照样停下来问人——而且被跳过依然不算数。

## 收尾契约：堵死“差不多做好了”

一个靠谱的技能必须规定死**最后几行怎么收尾**。比如 `/dev-story` 要求整次回复最后必须落在这几行固定格式上：

```text
Story: [path] — [Implemented | INCOMPLETE — <breakage> | BLOCKED — <reason>]
Run result: [OBSERVED — … | NOT VERIFIED — … | N/A — …]
Same-seed run: [仅从原型长出来的 Web 工程输出]
Next step: [...]
```

状态词被钉死在 `Implemented`、`INCOMPLETE`、`BLOCKED` 三选一里，每种状态精准绑定对应的下一步：没写完就继续 `/dev-story`，被依赖或未批准的 ADR 卡住就报解锁动作，干完了才指去 `/code-review` 或 `/story-done`。没有“基本完成、还差一点小优化”这种和稀泥的余地。

## 常见误解

- **误解一：`allowed-tools` 是沙箱，没列进去的工具技能绝对调不了。** 错。它只是免弹窗的**预批准列表**，不是权限边界；真要封死一个命令，得进 `settings.json` 的 `permissions.deny`。
- **误解二：把步骤写进 `SKILL.md` 就变成确定性程序了。** 不是。它依然是喂给大模型的自然语言剧本，模型还是有可能合并步骤或看漏条件；真正确定性的逻辑全部在 `!` 注入和 `.claude/scripts/` 的脚本里。
- **误解三：技能写得越长、把所有规则都抄进来越保险。** 恰恰相反。又长又啰嗦的 `SKILL.md` 一来烧上下文、二来压缩时容易被截断后半截，这正是 v1.2.0 之后把 14 个长技能拆成“精简主文件 + `references/`”的直接原因。

## 练习

1. 对比 `.claude/skills/dev-story/SKILL.md` 和 `.claude/skills/next-step/SKILL.md` 的 `allowed-tools` 与 `disable-model-invocation`，说说为什么前者严防模型自己启动、后者可以由模型随时调。
2. 如果你要给自己的项目写一个 `/release-notes` 技能，从 git 提交里整理更新日志，它的 `!` 注入命令、防呆边界（比如仓库压根没有 tag 或提交记录时怎么报）和收尾契约该怎么设计？
3. 为什么 v1.3.0 要把 28 条只读脚本白名单从各个技能的 `allowed-tools` 额外抄一份放进全局 `.claude/settings.json` 的 `permissions.allow`？

## 答案提示

1. `/dev-story` 会派代理改代码、改故事状态、改冲刺 YAML，产生真实副作用，必须由人显式触发；`/next-step` 是纯只读导航（不含 Write/Edit/Agent），模型在用户问“我下一步干嘛”时主动调它完全安全。
2. 可以用 `!` 注入 `git log` 或范围检查脚本的输出；若无提交或无新变更，收尾契约明确规定输出 `NO_CHANGES` / `NOT ASSESSED — no git history`，严禁模型凭空编造更新条目；写文件前必须走显式确认。
3. 因为 Claude Code 只在触发技能的第一轮生效 `SKILL.md` 的 `allowed-tools`；只要技能中途提问进入第二轮，技能再跑自己的只读脚本就会重新弹权限审批框。把纯只读脚本放进全局 `allow` 能彻底消除这类无意义弹窗，同时把写文件/跑业务代码的命令留在严格管控下。
