# 第 08 章 实施链路：`/dev-story` 怎么把故事变成代码

## 场景

故事已经就绪：`story-003-melee-parry.md`，Core 层，Logic 类型，ADR 已接受，依赖故事全部完成。你输入 `/dev-story production/epics/stealth/story-003-melee-parry.md`。

接下来发生的事情可以分成两条线：一条是文本处理线，决定模型看到什么；一条是实际执行线，决定磁盘上多出什么文件。这一章顺着两条线走一遍。

## 第一步：把故事变成事实表

技能调用 `story-facts.sh <story-path>`，拿到状态、类型、层、需求 ID、ADR、验收条件数量、测试证据状态、依赖。脚本只输出观察，不输出判决。

在没有故事的模板仓库上运行 `story-facts.sh --all`，输出是一张空表：

```
stories	0	production/epics/**/story-*.md
complete	0
in_review	0
in_progress	0
todo	0
blocked	0
other	0
no_status	0
```

`story-status.sh` 更短，只有一行 `STORIES none`。这两个脚本的价值在于：当模型问"有哪些故事可以做"时，答案来自磁盘，而不是来自记忆。

## 第二步：解析工作档位

技能注入的配置里有 `workflow`、`qa.level`、`gate_level`、`specialists`、`perf_budgets`、`system_overrides`。工作档位不是全局 rigor，而是按故事所属系统解析的：故事里的 `GDD:` 路径给出系统名，先查该系统的覆盖，再查项目值。

所以一个项目可以整体 minimal，只把战斗系统提到 full。此时战斗故事的 Phase 2 会要求需求注册表和 Accepted ADR，其他故事不受影响。

## 第三步：检查是否允许开始

Phase 2 是一张三列表，按档位给出不同要求：

| 输入 | full | standard | minimal |
|---|---|---|---|
| 需求注册表 | 缺失则停止 | 可选 | 不期待 |
| 故事点名的 ADR | 缺失或非 Accepted 则停止 | 只在点名时检查 | 只在点名时检查 |
| 控制清单 | 缺失则警告，继续 | 缺失则警告，继续 | 不期待 |

依赖检查独立于档位。每个依赖故事都要跑一次 `story-facts.sh`，状态不是 Complete 就停下来问用户：继续承担风险、先去完成依赖、还是它其实完成了只是状态没更新。

这里有一个细节：脚本读的是状态字段，不是 git 历史或文件内容。状态没更新，它就会认为没完成。仓库选择相信声明，同时把判断权交给用户。

## 第四步：确定代码根

写代码之前必须先回答"代码写到哪里"。`code-root-resolution.md` 给出的顺序是：

1. `engine.name` 从 `project.local.yaml` 再 `project.yaml` 读。
2. 旧版镜像 `.claude/docs/technical-preferences.md` 里的 `Engine:` 行。
3. 目录推断，但只在无歧义时：`src/`、`Assets/`、`Source/` 中恰好存在一个。
4. 否则：未解析。

未解析时不是默认到 `src/`，而是停止写入并报告。文档给出的理由很直接：Unity 项目里写到 `Assets/` 之外的代码不会被编译，也不会出现在编辑器里，工作安静地失效。

测试根同理。Unity 的测试要放 `Assets/Tests/EditMode/` 或 `PlayMode/`，放错位置的结果是测试运行器显示"0 tests, Passed"。这个输出看起来像通过，实际上是没跑。

## 第五步：选择执行者

Phase 4 用两张表。第一张按故事选程序员：

| 故事 | 角色 |
|---|---|
| Foundation 层，任意类型 | `engine-programmer` |
| 类型 UI | `ui-programmer` |
| 类型 Visual/Feel | `gameplay-programmer` |
| Core 或 Feature，玩法 | `gameplay-programmer` |
| Core 或 Feature，AI 或寻路 | `ai-programmer` |
| Core 或 Feature，网络 | `network-programmer` |

第二张按配置选引擎专家。`specialists` 行给出 `code`、`shader`、`ui`、`primary` 四个槽位，来自 `project.yaml`。例如 Godot C# 项目会配 `godot-csharp-specialist` 作为 `code`，这样即使 `engine.name` 只写 `Godot`，也能区分 GDScript 和 C#。

技能明确要求：不要凭记忆指定专家，以配置行为准。所有槽位都是 `unset` 且没有 `primary` 时，说明"未配置引擎专家"，然后继续，不阻塞。

## 第六步：构造简报

简报是整个链路里最像"工程"的部分。它不粘贴文档，只给路径和要点：

1. 故事文件本身，含验收标准、边界、QA 用例。
2. 每个需求 ID 在注册表里的匹配行，原文是权威。
3. ADR 的决策摘要和实施说明，**内联**，不给 ADR 路径。
4. 控制清单里对应层的规则，按章节摘。
5. `project.yaml` 的命名规范和注入的 `perf_budgets` 行。
6. 故事里测试证据的路径。

然后是测试要求，按 `qa.level` 分三档：

- minimal：明确告诉代理"不要写测试文件，测试证据在此档豁免"。这句话必须说出来，因为"省略一行"和"忘了要求"对代理来说无法区分。
- standard：测试与代码同时写，每条验收标准至少一个测试函数。禁止随机种子、时间依赖断言、外部 IO。
- full：同上，且每条标准都必须覆盖，`/story-done` 遇到未覆盖会阻断。

最后是输出契约：改了哪些文件、写了哪些测试函数、有没有问题或阻塞、是否完成。边界也写明：只在解析出的代码根下写代码，只在测试根下写测试；代码根未解析就什么都不写；不做一次性抽象；不为不可能发生的情况写错误处理；不为了让测试通过而特判。

## 第七步：检查产物而不是读报告

Phase 6 的第一条规则是：先看文件在不在。

> 代理报告里点名的文件如果在磁盘上不存在，这一步就是失败的，不管报告写得多流畅。

这条规则来自 `error-recovery-protocol.md` 的"触发器 0"。文档描述了一种具体的失败形态：并行的子代理做了大量工作，然后返回一段像样的开场白，没有路径、没有摘要、没有 BLOCKED 标记，也没有写任何文件。父会话读到这段文字，以为阶段完成了，实际上半个并行阶段消失了。

所以判断依据是产物，不是转录。

## 第八步：解析检查与运行观察

解析检查因引擎而异，Godot 的命令写得很具体：

```bash
godot --headless --path . --import
godot --headless --path . -s res://.claude/scripts/godot-parse-check.gd -- res://<changed.gd>
```

第二条退出码 1 表示有脚本没加载，输出里的 `PARSE FAIL:` 会点名是哪个。技能特别提醒：不要用 `--check-only`，只跑 `--import` 也不算解析检查。

引擎二进制不存在时，结果必须写成 `parse NOT VERIFIED — engine binary not available`，不允许读一遍代码就断言"应该能解析"。

运行观察针对玩家能看到的故事。步骤是：直接启动到故事改动的场景，截图保存到 `production/qa/evidence/<story-slug>/`，用 `review-receipts.sh hash` 给改动文件打内容哈希，存成 `stamp.txt`，然后打开图片与验收标准比对。

最后只输出一行：

```
Run result: OBSERVED — <屏幕上是什么>
Run result: NOT VERIFIED — <原因>
Run result: N/A — <为什么没有可观察内容>
```

`N/A` 的原因不能是"这是个逻辑故事"，因为逻辑故事也可能有可见结果。这个限制防止用类型标签逃避观察。

## 第九步：收尾

Phase 7 输出固定结构：改动文件、测试证据、验证命令与结果、逐条验收标准、偏差、引擎风险、阻塞。然后把实际改动写入故事的 `## Files` 段，替换计划清单。

再写会话检查点。检查点包含更新日期、分支、当前任务、下一步、阻塞项、进行中的文件、运行结果、未决问题。它是下次会话恢复工作的唯一依据。

最后一行是收尾块，三行，状态词只有 Implemented、INCOMPLETE、BLOCKED 三种。

## 常见误解

误解一：代理说完成就是完成。检查点在产物：文件、测试、解析结果、截图。

误解二：解析通过等于能运行。解析只说明代码能加载，不说明行为正确，所以还要运行观察。

误解三：测试文件存在等于测试通过。`/dev-story` 和 `/story-done` 都只检查存在性，通过与否要用户自己跑测试套件，仓库在提示里明确要求用户先跑再关闭故事。

## 练习

1. 在模板仓库上运行 `story-facts.sh --all`，解释每列含义。
2. 假设引擎是 Unity，代码根解析失败，`/dev-story` 应该做什么？为什么不能默认写到 `src/`？
3. 为一个 Visual/Feel 故事列出从实施到关闭需要的全部证据。

## 答案提示

1. 第一列是统计项，第二列是数量，第三列是搜索路径。全零表示 `production/epics/` 下没有故事。
2. 停止写入并报告未解析的代码根。默认到 `src/` 在 Unity 里不会编译，工作会安静失效。
3. 代码与测试、解析检查结果、运行到目标场景的截图、截图目录下的 `stamp.txt`、`<story-slug>-evidence.md` 里的签字行，以及 `/story-done` 的逐条核对表。
