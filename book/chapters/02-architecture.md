# 第 02 章 总体架构：一个会话，四种约束

## 场景

第一次打开这个仓库，目录树看起来像一份规范文档的合集：`.claude/` 下面有 agents、skills、hooks、rules、docs、scripts 六个子目录，根目录有 `CLAUDE.md` 和 `project.yaml`，再往下是 `design/`、`docs/`、`production/`、`studio-tests/`。没有 `package.json`，没有 `Dockerfile`，没有服务入口。

有人会问：这东西怎么运行？

答案是：它不自己运行。Claude Code 启动时读取当前目录的 `CLAUDE.md` 和设置文件，把一部分文本放进上下文，把一部分命令注册成事件回调。你输入斜杠命令时，Claude Code 找到对应的技能文件，把正文交给模型，模型再按正文里的步骤调用工具。所谓"工作室"，是这一串加载与调用的结果。

## 四种约束

把仓库里的所有机制按"约束力从软到硬"排队，只有四层。

第一层是常驻上下文。`CLAUDE.md` 用 `@path` 语法导入其他文档，例如 `@.claude/docs/directory-structure.md` 和 `@.claude/docs/coordination-rules.md`。每个会话开始都会带上这些内容，模型看得见，但可以忽略。这一层最软。

第二层是按需加载。技能的 `SKILL.md` 正文在调用时进入上下文；参考文档要模型主动读；Agent 提示词在派生子代理时加载。范围比第一层窄，内容更具体，仍然只是文字。

第三层是事件回调。`settings.json` 把 15 个命令挂到 8 类事件上：SessionStart、PreToolUse、PostToolUse、Notification、PreCompact、Stop、SubagentStart、SubagentStop。这些脚本能读到工具调用的完整参数，能打印警告，也能用特定退出码改变行为。

![四种约束：从常驻提示词到宿主权限，强制力逐级上升](../../wiki/assets/diagrams/four-layers.svg)

第四层是宿主权限。`settings.json` 的 `permissions` 段列出允许和拒绝的命令模式。例如 `Bash(rm -rf *)`、`Bash(git push --force*)`、`Read(**/.env*)` 在 deny 列表里。这一层由 Claude Code 自己执行，不依赖模型配合。

四层的强制力差别很大。第四层是真正的外科手术刀，第三层只有部分事件能阻断，前两层是建议。

## 三种状态，三种生命周期

仓库里的文件按生命周期可以分成三类，混在一起会读得很乱。

永久资产随仓库走：`.claude/agents/`、`.claude/skills/`、`.claude/rules/`、`.claude/docs/templates/`、`studio-tests/`。这些是模板本体，克隆下来就带着。

项目状态随你的游戏走：`project.yaml` 描述引擎和模式；`design/` 放设计文档和注册表；`docs/architecture/` 放 ADR 和控制清单；`production/epics/` 放故事；`production/sprints/` 放迭代计划。这些一开始基本是空的或占位符。

会话状态随一次工作走：`production/session-state/active.md` 是检查点，`production/session-logs/` 是日志。这两处在 `.gitignore` 里，不进版本控制。

分类的意义在于知道什么可以改、什么不该改。修改 `.claude/skills/` 是定制模板，会被上游更新覆盖；修改 `production/epics/` 是推进项目；清理 `production/session-state/` 只影响当前会话的恢复能力。

## 目录与代码根

`CLAUDE.md` 导入的 `directory-structure.md` 给出一张表，说明各目录职责。其中最容易被忽略的一条是：代码根由引擎决定，`src/` 只是 Godot 那一行。

| 引擎 | 代码根 | 测试根 |
|---|---|---|
| Godot | `src/` | `tests/unit/`、`tests/integration/` |
| Unity | `Assets/` | `Assets/Tests/EditMode/`、`Assets/Tests/PlayMode/` |
| Unreal | `Source/<Module>/` | `Source/<Module>/Private/Tests/` |

这不是风格偏好。Unity 只编译 `Assets/` 和 `Packages/` 下的代码，UnrealBuildTool 只发现 `Source/` 下的模块。把代码写到 `src/` 在 Unity 项目里不会报错，它会安静地不参与编译。这个坑在第 14 章会展开，因为它解释了仓库里大量 `resolve_code_root` 逻辑的存在理由。

## 一次会话的加载顺序

把时序拉直，一次典型会话是这样开始的：

1. Claude Code 在项目根启动，读取 `CLAUDE.md`，展开其中的 `@` 导入，把 `directory-structure.md`、`coordination-rules.md`、`coding-standards.md` 和引擎版本引用一起装进上下文。
2. 读取 `.claude/settings.json`，注册 Hook 和权限规则，设置状态栏命令。
3. 触发 SessionStart 事件，`session-start.sh` 检查 `production/session-state/active.md`，如果有检查点就预览；`detect-gaps.sh` 检查项目缺什么。
4. 模型看到这些内容，等待你的第一条消息。
5. 你输入 `/dev-story`，Claude Code 找到 `.claude/skills/dev-story/SKILL.md`，执行正文开头那条被反引号包住的 shell 命令，把配置解析结果注入上下文，然后把正文交给模型。
6. 模型按正文的 Phase 1 到 Phase 7 执行，期间每次写文件都会经过 PreToolUse Hook。

这条链上只有第 5 步的 shell 注入是"先执行再看"，其余都是"先看再决定"。理解这一点，就理解了为什么技能正文里那些 `!` 开头的命令行如此重要：它们把配置求值的结果直接塞进提示词，不依赖模型自己去读文件、拼路径、猜默认值。

## 40 KB 的读保护

架构里有一个小设计值得单独说。`validate-read.sh` 挂在 PreToolUse 的 Read 事件上，只监视三类路径：`design/`、`docs/architecture/`、`production/session-state/`。当一次读取既没有 offset 也没有 limit，且文件超过 40 KB 时，脚本拒绝这次读取，`exit 2`，并在 stderr 里列出该文件的各级标题和行号。

这个设计的意图写在文件头：一次被拒绝的读取花掉一个回合，而它拦下的那次读取可能花掉几万 token。因为按范围读取总能通过，不会有工作被永久卡住。

它同时示范了这套架构的一种价值观：宁可让模型多走一步，也不要把整个大文件塞进上下文。`effects-map.md` 那份配置规范被反复提醒"不要在技能运行时读它"，理由是它的体积比 `CLAUDE.md` 每会话加载的全部内容还大若干倍。

## 常见误解

误解一：以为 `.claude/docs/` 下的文档都会自动加载。实际上只有 `CLAUDE.md` 里用 `@` 导入的才常驻，其余要按需读取，仓库还专门设计了读保护来防止误读。

误解二：以为 `settings.json` 里的 deny 列表就是全部安全边界。它只覆盖 Bash 和 PowerShell 的命令模式，写文件路径的检查在 Hook 里，而且多数只警告。

误解三：以为技能是脚本。技能正文是给模型看的步骤说明，可以被模型理解、跳过、改写；真正确定性的部分都在 `scripts/` 和 `hooks/` 的 Bash 里。

## 练习

1. 列出 `settings.json` 中注册的 Hook 事件，并指出哪些事件的退出码 2 会阻断操作。
2. 解释为什么 `validate-read.sh` 只监视三个目录，而不是全仓库。
3. 如果你的项目用 Unity，`CLAUDE.md` 里有一行导入 `@docs/engine-reference/godot/VERSION.md`，这行会造成什么问题？`/setup-engine` 会怎么处理它？

## 答案提示

1. 八个事件：SessionStart、PreToolUse、PostToolUse、Notification、PreCompact、Stop、SubagentStart、SubagentStop。能阻断的是 PreToolUse，Stop 和 SubagentStop 的退出码 2 会阻止停止，PreCompact 可以阻止压缩；其余事件退出码 2 只影响提示的去向。以官方 Hook 文档为准。
2. 三个目录是大型设计文档和状态文件的集中地，也是最容易一次读满上下文的地方。全仓库拦截会误伤代码阅读，成本高于收益。
3. 那行是注释标记的引擎引用导入，默认指向 Godot。Unity 项目每次会话都会加载无关的 Godot 版本说明。`/setup-engine` 会把它改写成 `@docs/engine-reference/unity/VERSION.md`。
