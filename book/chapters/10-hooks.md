# 第 10 章 Hook：十五个检查点里谁真的能拦住

## 场景

你在故事文件上执行一次 Edit，把 `Status: Ready` 改成 `In Progress`。写入发生前，`validate-write.sh` 收到一条 JSON，里面有工具名、文件路径和新内容。它检查这个文件是否属于"永不覆盖"清单、配置是否写到该写的位置、原型目录有没有被生产代码引用。发现问题时它打印一段警告，然后退出码为 0。

同一时刻，你试图整篇读取一份 60 KB 的设计文档。`validate-read.sh` 拒绝，退出码 2，把文件的所有标题和行号打给你。

两个 Hook，一个劝阻，一个拦住。这一章把 15 个注册命令逐个归类。

## 注册表

`.claude/settings.json` 的 `hooks` 段把命令挂到事件上。快照里共有 15 条命令，分布在 8 个事件：

| 事件 | 命令 | 数量 |
|---|---|---|
| SessionStart | `session-start.sh`、`detect-gaps.sh` | 2 |
| PreToolUse（Bash/PowerShell） | `validate-commit.sh`、`validate-push.sh` | 2 |
| PreToolUse（Write/Edit） | `validate-registry.sh`、`validate-write.sh` | 2 |
| PreToolUse（Read） | `validate-read.sh` | 1 |
| PostToolUse（Write/Edit） | `validate-assets.sh`、`validate-skill-change.sh` | 2 |
| Notification | `notify.sh` | 1 |
| PreCompact | `pre-compact.sh` | 1 |
| Stop | `session-stop.sh` | 1 |
| SubagentStart | `log-agent.sh` | 1 |
| SubagentStop | `log-agent-stop.sh`、`validate-agent-artifact.sh` | 2 |

`hooks/` 目录里另外有三个脚本没有注册：`yaml-helper.sh` 是被 source 的库，`log-instructions.sh` 和 `update-check.sh` 需要手动或由其他脚本调用。所以"15 个 Hook"和"18 个脚本"都对，口径不同。

## 能拦住的

真正能阻断的有三处。

`validate-read.sh` 用 `exit 2` 拒绝超限的整篇读取。它是唯一一个在 PreToolUse 阶段硬拦的验证 Hook。拒绝时它不是简单说"不行"，而是列出标题和行号，告诉模型该怎么分段读。这符合"拒绝要给替代路径"的原则。

`validate-assets.sh` 在 PostToolUse 阶段对无效 JSON 用 `exit 2`。注意 PostToolUse 发生在写入之后，文件已经落盘，所以它不是"阻止写入"，而是"让模型看到自己写坏了"。脚本头部把这件事说得很清楚：

> PostToolUse Hook 无法阻断，写入已经发生。唯一的问题是通知谁，而退出码决定这个：exit 1 只给用户看，模型以为写干净了继续往下走；exit 2 把 stderr 作为可操作反馈交给模型，它能修正刚写的文件。

`validate-commit.sh` 的阻断范围很窄：只有暂存了 `assets/data/`、`Assets/Data/`、`Content/Data/` 等路径下的 JSON，且校验失败或无法校验时才 `exit 2`。其余检查，包括 GDD 章节完整性、硬编码数值、无主 TODO，都只是追加到警告列表，最后 `exit 0`。

## 只提醒的

`validate-write.sh` 是最容易被高估的一个。它的名字像守门员，实际行为写在文件头：

```
exit 0 always = advisory (it warns, never blocks)
```

它检查的项目不少：故事文件是否被覆盖、配置枚举是否合法、本地配置是否写了不可本地覆盖的键、评审模式是否被钉死、原型目录与生产代码是否互相引用、字符串冻结期间是否改了文案、子代理是否越界写文件。

每一项都有真实价值，但它们全部走警告通道。`skill-authoring.md` 要求"跳过的步骤要自己说出来"，这个脚本遵守了：无法检查时会打印 `Write check skipped: ...`，而不是安静放行。

`validate-registry.sh`、`validate-agent-artifact.sh`、`validate-skill-change.sh` 同样是建议级。`validate-push.sh` 更直接：它检测到你在往受保护分支推送时，输出一段 JSON，其中 `additionalContext` 会作为上下文给模型看，`systemMessage` 给用户看。脚本里甚至留了一行注释，说明如果要改成阻断，把 `printf` 换成 `echo` 加 `exit 2` 即可。

## 记录型的

SessionStart 的两个脚本负责恢复和体检。`session-start.sh` 读 `production/session-state/active.md`，把检查点区域预览出来；这个区域被要求控制在 25 行以内，可以原样展示。`detect-gaps.sh` 检查项目缺什么。

`pre-compact.sh` 在上下文压缩前触发，提醒保存状态。官方文档里 PreCompact 的退出码 2 可以阻止压缩，但这个脚本没有使用阻断，只是提示。

`log-agent.sh`、`log-agent-stop.sh`、`session-stop.sh` 写审计日志。`notify.sh` 在权限提示或空闲提示时发桌面通知，Windows 走 PowerShell，其他平台目前是空操作。

## Hook 的输入从哪来

每个 Hook 从标准输入拿到一段 JSON。`validate-write.sh` 的注释给出了两种形态：

```json
{"tool_name":"Write","tool_input":{"file_path":"...","content":"..."}}
{"tool_name":"Edit","tool_input":{"file_path":"...","old_string":"...","new_string":"...","replace_all":false}}
```

编辑操作没有完整的新文件内容，只有替换片段。所以 Hook 调用 `hook-input.sh --new <tmp>` 重建写入后的文件，再交给 `write-guard.sh` 判断。重建失败时，依赖内容的规则（配置、原型）会明确说没有检查，依赖路径的规则继续运行。

这段设计体现了一个原则：检查器要能区分"检查通过"和"没检查"。`write-guard.sh` 输出的第一行是 `checked <n> rules`，让调用方知道跑了多少条。

## 警告怎么送达

早期的做法是往 stderr 打印，然后 `exit 0`。问题在于，退出码 0 的 stderr 只进调试日志，用户和模型都看不到。脚本注释里记录了这个问题：警告被写进了没人读的地方。

现在的做法是调用 `yaml-helper.sh` 里的 `hook_warn`，输出一段结构化 JSON，包含 `systemMessage` 和 `hookSpecificOutput.additionalContext`。前者给用户，后者给模型。没有这个函数时回退到 stderr。

这个细节值得学：Hook 的输出通道比输出内容更容易出错。一条正确的警告发到错误的通道，等于没发。

## 官方语义对照

用 Context7 查 Claude Code 官方 Hook 文档，确认了几条与本仓库实现对应的规则：

- PreToolUse 的 `exit 2` 阻断工具调用，stderr 作为阻断原因反馈给模型。
- PostToolUse 的 `exit 2` 不能撤销已发生的操作，只把 stderr 作为反馈交给模型。
- 其他非零退出码属于非阻断错误，通知里带 stderr 的第一行。
- `exit 0` 且输出合法 JSON 时，JSON 字段生效。

这解释了为什么 `validate-assets.sh` 明知写入已经发生还要用 `exit 2`：它要的不是撤销，而是让模型修。

同时要提醒：Hook 的语义在不同版本间有过调整，尤其是"谁看到 stderr"。仓库里 `validate-assets.sh` 的注释认为 `exit 1` 只给用户看，这和某些版本文档的描述不完全一致。移植这套 Hook 时，应以你当前 Claude Code 版本的官方文档为准，并写一个最小实验确认。

## 权限与 Hook 的分工

`settings.json` 的 `permissions.deny` 是另一层。它列出 `rm -rf` 的各种变体、`git push --force` 的各种变体、`sudo`、`chmod 777`、读 `.env`、编辑 `.uasset` 等。

这一层由宿主执行，比 Hook 更硬，但它只匹配命令字符串。`validate-push.sh` 的存在说明作者不完全信任字符串匹配：它额外解析 git 命令的分段、处理 `&&` 链接、跳过引号里的文本、识别 `git -C` 等变体，才判断这是不是一次推送。

两层的分工可以概括为：权限层挡住明确危险的动作，Hook 层处理需要上下文判断的规则。

## 常见误解

误解一：有 Hook 就有安全边界。15 个里只有 3 处会阻断，其余是提醒或记录。

误解二：PostToolUse 能撤销坏写入。它只能在写入后告知，修复要靠模型或人。

误解三：Hook 一定在项目根运行。脚本开头都有一段根目录解析逻辑，因为工作目录不对会读写错误的树。这段逻辑的优先级是：当前目录有 `project.yaml` 或 `.claude/` 就用当前目录，否则用 `CLAUDE_PROJECT_DIR`，最后回退到脚本自身位置。

## 练习

1. 从 `settings.json` 数出所有 Hook 命令，按"阻断、反馈、记录"分类。
2. 解释 `validate-read.sh` 为什么要在 stderr 里列出标题和行号，而不是只说文件太大。
3. 把 `validate-push.sh` 改成真正阻断受保护分支推送，需要改哪一行？会带来什么后果？

## 答案提示

1. 阻断：`validate-read.sh`；反馈：`validate-assets.sh`、`validate-commit.sh`（仅数据 JSON）；其余为提醒或记录。
2. 拒绝必须给出可执行的替代路径，否则模型会重试同样的读取。列出标题让它能按范围读，一次拒绝就完成教学。
3. 把输出 JSON 的那段替换为 `echo "BLOCKED: ..." >&2; exit 2`。后果是所有受保护分支的推送都被硬拦，包括紧急修复；需要额外的绕过机制或人工在本地改脚本。
