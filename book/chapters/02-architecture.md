# 第 02 章 总体架构：一个会话，四种约束

## 先拆穿外壳：它到底怎么跑起来的

第一次克隆 CCGS，打开目录树往往会愣一下：`.claude/` 里塞着 `agents/`、`skills/`、`hooks/`、`rules/`、`docs/`、`scripts/`、`genres/`、`engines/` 八个子目录，根目录放着 `CLAUDE.md`、`project.yaml`，旁边还有 `design/`、`docs/`、`production/`、`prototypes/`、`studio-tests/`。既没有后台守护进程，也没有 `docker-compose.yml`。

它到底怎么运行？

全靠宿主 **Claude Code**。当你在项目根目录敲下 `claude` 的那一刻，Claude Code 自动读入当前目录的 `CLAUDE.md` 和 `.claude/settings.json`：把该常驻的规矩塞进模型上下文，把权限表和 15 条 Hook 挂到工具调用的生命周期里。等你敲下 `/prototype` 或 `/dev-story`，宿主去找到对应的 `SKILL.md`，先执行正文开头带 `!` 的命令把配置算清楚贴进去，再把剧本交给模型一步步调工具。

所以，**必须从项目根目录启动 Claude Code**。如果你在 `src/` 子目录里启动它，宿主根本加载不到根目录的 `settings.json`，所有的 Hook、高危命令拦截和默认确认模式都会直接失效（`CLAUDE.md` 里专门写了条兜底提醒，一旦发现启动目录不对就先警告）。

## 按约束力从软到硬排排坐

搞懂整仓架构最省脑子的办法，是别按目录背清单，而是按**“到底能不能卡住大模型”**排成四层：

![四种约束：从常驻提示词到宿主权限，强制力逐级上升](../../wiki/assets/diagrams/four-layers.svg)

- **第 1 层：常驻上下文（极软，贴墙标语）**。`CLAUDE.md` 以及里面用 `@` 语法导入的 `directory-structure.md`、`coordination-rules.md`、`coding-standards.md`。只要开会话就一定带进去。注意 v1.3.0 做了个很聪明的减法：**模板默认不再硬塞 Godot 的版本参考文档**，直到你真的定了引擎（跑 `/setup-engine`、原型 Grow 落盘，或改 `engine.name`），脚本才把对应引擎的 `@docs/engine-reference/<engine>/VERSION.md` 插进去，免得白白浪费上下文，或者让做网页游戏的会话满脑子都是 Godot API。但归根结底，这一层全是文字，模型忙起来随时会忘。
- **第 2 层：按需加载的剧本与资料（软，但夹带了确定性注入）**。包括 49 个角色文件、78 个 `SKILL.md`（75 个正式技能 + 3 个旧名转发）、14 条路径规则、73 份品类知识文件。它们平时不占地方，触发了才加载。这一层最靠谱的一手，是技能正文顶部的 `!` 命令注入——把配置解析、故事状态统计这类确定性计算先用 Bash 算死，直接把结果贴给模型看，不给它瞎猜的机会。
- **第 3 层：生命周期 Hook（半硬，15 条里只有 3 处真拦）**。`.claude/settings.json` 在 8 类事件上挂了 15 条命令（`.claude/hooks/` 目录里共 18 个脚本，另外 3 个是库和未注册辅助脚本）。脚本能拿到工具调用的完整 JSON 参数，但真正用 `exit 2` 拍桌子的只有三处：`validate-read.sh` 拦超 40 KB 大文档整篇读取、`validate-commit.sh` 拦格式写坏的暂存数据 JSON、`validate-assets.sh` 在写坏 JSON 后把报错拍回模型脸上让它返工。其余大多数 Hook（包括名头很响的 `validate-write.sh`）全是 `exit 0` 发提醒，拦不住。
- **第 4 层：宿主权限表（真硬，不看模型脸色）**。`.claude/settings.json` 的 `permissions` 段，由 Claude Code 宿主直接执行。`deny` 列表把 `rm -rf` 的二十来种写法、`git push --force`、`git reset --hard`、`sudo`、`chmod 777`、读写 `.env*`、编辑 `.uasset`/`.umap` 直接封死；v1.3.0 还把 `allow` 列表扩充到了 31 条（新增 28 条只读框架脚本和 `yaml-helper.sh` 7 个只读函数），因为 Claude Code 对技能自带的 `allowed-tools` 只在技能启动那一轮生效，不放进全局 `allow`，技能每问你一个问题后下一轮又要重新弹窗要授权。

## 仓库里三类文件，千万别混着管

把文件按生命周期拆成三类，升级模板和清理垃圾时才不会误伤：

1. **框架本体（跟着上游版本走）**：`.claude/agents/`、`.claude/skills/`、`.claude/hooks/`、`.claude/scripts/`、`.claude/rules/`、`.claude/genres/`、`.claude/engines/`、`.claude/docs/templates/`、`studio-tests/`。升级 CCGS 时这些目录大都可以按 `UPGRADING.md` 整块覆盖（除了你自己改过的配置和 `.claude/docs/technical-preferences.md`）。
2. **你的项目资产（跟着游戏进 Git）**：`project.yaml`、`CLAUDE.md`、`design/`（含 `game-brief.md`、GDD、实体注册表）、`docs/`（架构、ADR、控制清单）、`prototypes/`（单文件可玩原型）、`references/`（你丢进去的美术/音效参考）、`src/` 或引擎代码根、`assets/`、`tests/`、`production/epics/`。
3. **个人与会话临时态（被 `.gitignore` 拦在仓库外）**：`project.local.yaml`（你的个人偏好覆盖）、`production/session-state/active.md`（断点续传检查点）、`production/session-logs/`（归档日志与决策日志）、`.claude/worktrees/`（隔离工作树）。

顺带一提，v1.2.0 之后仓库根目录多了一个 `.worktreeinclude`，里面列着 `project.local.yaml`、`CLAUDE.local.md` 和 `.claude/settings.local.json`，配合 `settings.json` 里的 `"worktree": { "baseRef": "head" }`，保证隔离出来的原型分支或子代理工作树是从你当前本地提交切出来的，还能自动带上你的个人配置，同时绝不把 `.env` 这类密钥带进去。

## 四大引擎的代码根：为什么不再硬写 `src/`

以前很多脚本写死了扫 `src/`，一换引擎全军覆没。v1.3.0 把四个一等公民引擎的目录和默认命令统一收进了一张制表符分隔的总表 `.claude/engines/engines.tsv`：

| 引擎 | 默认代码根 | 默认测试根 | 默认资产根 | 为什么不能随便写进 `src/` |
|---|---|---|---|---|
| **Web** | `src/` | `tests/` | `assets/` | Vite 从 `index.html` 入口打包；扁平网页项目还可用 `engine.code_root: .` |
| **Godot 4** | `src/` | `tests/` | `assets/` | Godot 的 `res://` 扫全仓，无强限制 |
| **Unity** | `Assets/` | `Assets/Tests/` | `Assets/` | Unity **只编译 `Assets/` 和 `Packages/`**，写到 `src/` 压根不进构建 |
| **Unreal 5** | `Source/` | `Source/<Module>/Private/Tests/` | `Content/` | UnrealBuildTool 只认 `Source/` 下的模块 |

所有 Hook、脚本和技能都通过 `engine-row.awk` 和 `resolve_code_root()` 读同一张表，绝不各自维护一份引擎分支。如果项目目录非标准，还可以在 `project.yaml` 里填 `engine.code_root` 和 `engine.test_root`，具体解析坑点第 13 章细拆。

## 一次典型会话的时间线

把从打开终端到跑完一条命令的顺序拉直，大概就这六步：

1. 在根目录执行 `claude`，宿主读 `CLAUDE.md`（展开 `@` 导入）和 `.claude/settings.json`（挂权限、状态栏和 15 条 Hook）。
2. 触发 `SessionStart`：`session-start.sh` 展示分支、最近提交和 `active.md` 里的检查点（还会顺手在后台每天最多查一次 GitHub 有没有新版，CI 环境下自动关闭）；`detect-gaps.sh` 扫描仓库状态，空白项目直接提醒你去跑 `/prototype` 或 `/start`。
3. 你敲下一条斜杠命令（比如 `/dev-story` 或 `/prototype`）。
4. 宿主找到对应 `SKILL.md`，先执行正文开头的 `!` 命令，把配置求值结果或故事列表直接贴进提示词。
5. 模型照着剧本推进，需要派活时按规则拉起子代理。
6. 期间每一次 `Read`、`Write`、`Edit`、`Bash` 工具调用，都要先过 `permissions.deny`，再过 `PreToolUse` Hook，落盘后再走 `PostToolUse` Hook。

## 40 KB 读保护：一个很贼的省钱设计

在所有 Hook 里，有个极实用又容易被抄走的小机关：`validate-read.sh`。它专门蹲在 `design/`、`docs/architecture/`、`production/session-state/` 这三个大文档聚集地门口。

只要模型犯懒，想一口气把超过 40 KB（可通过 `features.read_guard_kb` 调，也可以 `features.read_guard: off` 关掉）的文档整篇吞进上下文——也就是调用 `Read` 时既不传 `offset` 也不传 `limit`——脚本直接给它吃个闭门羹（`exit 2`），同时把这篇文档最多 40 个 Markdown 标题和对应行号甩在 `stderr` 里：“别整本硬背，自己挑要看的那一节，带行号范围重读。”

多折腾这一来一回，成本只是一轮工具调用，换回来的是少烧几万 token，上下文还不至于瞬间塞爆。因为只要带了行号范围就一定放行，绝不会把任何任务永久卡死。连脚本里都写了快速逃生路径：平时读普通代码文件时，纯用 Bash 字符串匹配判断路径里不含那三个目录名，直接 `exit 0` 溜走，连 `jq` 和子进程都不起。

## 常见误解

- **误解一：`.claude/docs/` 里的几十份规范每次开会话都会自动读进去。** 不会。只有 `CLAUDE.md` 里 `@` 点名的几份常驻，像 `effects-map.md` 这种巨型配置字典还被反复警告“禁止技能运行时整篇读取”。
- **误解二：有 `settings.json` 的 `deny` 列表就等于有了沙箱。** `deny` 只认匹配到的命令字符串模式，管不到未列举的破坏性命令，也挡不住跨工具绕过；文件写入检查在 Hook 里，且多为告警。
- **误解三：写进 `SKILL.md` 的步骤像代码一样绝对按顺序执行。** `SKILL.md` 本质还是给模型看的自然语言流程，模型依然可能偷懒跳步；真正百分百确定的，只有 `.claude/scripts/` 和 `.claude/hooks/` 里的脚本。

## 练习

1. 打开 `.claude/settings.json`，数出注册了 Hook 的 8 个事件，并结合 Claude Code 机制区分哪些事件的 `exit 2` 真能拦住动作，哪些只是把错误喂回给模型。
2. 想想看：`validate-read.sh` 为什么只盯 `design/`、`docs/architecture/`、`production/session-state/` 三个目录，而不对全仓库所有超 40 KB 文件一刀切？
3. 在 v1.3.0 里，为什么模板自带的 `CLAUDE.md` 默认把引擎参考的 `@docs/engine-reference/.../VERSION.md` 导入行留空了？如果你手动改了 `project.yaml` 里的 `engine.name` 却忘了改 `CLAUDE.md`，会发生什么？

## 答案提示

1. 8 个事件是 `SessionStart`、`PreToolUse`、`PostToolUse`、`Notification`、`PreCompact`、`Stop`、`SubagentStart`、`SubagentStop`。`PreToolUse` 的 `exit 2` 在动作发生前直接拦停；`PostToolUse` 已经落盘，只能把 stderr 反馈给模型让它修；`Stop` / `SubagentStop` 返回 `exit 2` 可阻止会话/子代理提前结束。
2. 这三个目录是长篇 GDD、架构方案和会话日志的重灾区；如果全仓一刀切，连读一个稍大的源文件或锁文件都被拦，反而添乱。
3. 留空是为了避免还没定引擎（或者做 Web 原型）的项目白白加载 Godot 4.7 的文档污染上下文。如果你手动填了 `engine.name` 却没插导入行，`session-start.sh` 会在开会话时发出警告，而用 `/setup-engine` 或 `/project-settings engine.name=<引擎>` 会自动帮你把那行写进去。
