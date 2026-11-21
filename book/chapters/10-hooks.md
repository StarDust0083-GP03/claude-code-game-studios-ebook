# 第 10 章 Hook：十五个检查点里，到底谁真的能拦住

## 先卸妆：挂了 15 个 Hook，不等于有 15 道门禁

不少人一看到 `.claude/settings.json` 里满满当当注册了 15 条 Hook 命令，下意识就觉得：“稳了，AI 乱改文件、乱推代码肯定全被 Hook 拦住了。”

真把这 15 个脚本一个个翻开看退出码，真相会让你凉半截：**15 条注册命令里，真用 `exit 2` 拍桌子的只有 3 处，而且其中 1 处还是写完之后才喊返工。**名头最唬人的 `validate-write.sh` 和 `validate-push.sh`，永远返回 `exit 0`——纯属口头劝阻。

把这件事彻底拆透，才不会对着一个根本不拦人的警报器产生虚假安全感。

## 15 条注册命令 vs 18 个脚本的全景账

`.claude/hooks/` 目录里躺着 **18 个** `.sh` 脚本，但 `.claude/settings.json` 注册了 **15 条**命令，挂在 8 类事件上：

| 生命周期事件 | 注册脚本 | 真实威力 |
|---|---|---|
| `SessionStart` | `session-start.sh`、`detect-gaps.sh` | 展示检查点、缺口和版本更新提醒（纯信息，v1.3.0 超时升到 20s） |
| `PreToolUse`（Bash / PowerShell） | `validate-commit.sh`、`validate-push.sh` | **窄阻断**（仅数据 JSON 坏了或无 Python 时 `exit 2`）/ 仅警告 |
| `PreToolUse`（Write / Edit） | `validate-registry.sh`、`validate-write.sh` | 仅警告（永远 `exit 0`） |
| `PreToolUse`（Read） | `validate-read.sh` | **硬阻断**（超 40 KB 整篇读取直接 `exit 2`） |
| `PostToolUse`（Write / Edit） | `validate-assets.sh`、`validate-skill-change.sh` | **写后反馈**（写坏数据 JSON 用 `exit 2` 拍回模型）/ 仅提醒 |
| `Notification` | `notify.sh` | Windows PowerShell 弹窗通知（其他系统空操作） |
| `PreCompact` | `pre-compact.sh` | 只记日志（不阻断压缩） |
| `Stop` | `session-stop.sh` | 异步后台归档 `active.md` 与 git 活动（`async: true`，不卡回复） |
| `SubagentStart` | `log-agent.sh` | 记子代理启动审计日志 |
| `SubagentStop` | `log-agent-stop.sh`、`validate-agent-artifact.sh` | 记停止日志 / 核对简报点名产物是否落盘（仅告警） |

![十五个注册命令按事件分组，只有少数会阻断](../../wiki/assets/diagrams/hook-map.svg)

另外 3 个没注册在 `settings.json` 里的脚本分别是：`yaml-helper.sh`（给全仓 `source` 的核心配置库）、`update-check.sh`（被 `session-start.sh` 调用的版本更新后台检查器）、`log-instructions.sh`（留给你按需自己挂载的指令诊断脚本）。

## 唯一真用 `exit 2` 的三处

1. **`validate-read.sh`（真硬拦）**：全仓唯一一个在动作发生前直接拦人的验证 Hook。蹲在 `design/`、`docs/architecture/`、`production/session-state/` 门口，只要模型不带 `offset` / `limit` 想硬吞超 40 KB 大文档，直接 `exit 2` 拒读，并把最多 40 个章节标题和行号打在 stderr 里教它分段读。拒绝的同时给清替代路径，模型绝不会卡死。
2. **`validate-commit.sh`（极窄硬拦）**：只在暂存区包含 `assets/data/`、`Assets/Data/`、`Content/Data/` 等路径下的 JSON 文件，且 JSON 语法坏了（或机器没装 Python 没法验）时 `exit 2` 拦停提交。至于硬编码数值、GDD 缺节、无主 TODO，统统只追加警告然后 `exit 0` 放行。顺便一提，v1.3.0 修了个社区报上来的真 bug（#155）：以前没有 Python 的机器上 `git commit -m "msg" -a` 会漏掉跟在提交信息后面的 `-a` / `--all`，导致修改的数据文件没经检查直接进了提交，现在已经补齐识别。
3. **`validate-assets.sh`（写后拍桌子）**：挂在 `PostToolUse` 上，触发时文件其实已经落盘了，根本撤不回。那它为什么还要在写坏 JSON 时 `exit 2`？脚本头部写得特别通透：**在 PostToolUse 里，`exit 1` 的报错只给用户看，模型根本不知道自己写坏了会接着往下走；而 `exit 2` 会把 stderr 作为可操作反馈直接拍回模型脸上，逼它立刻把刚写坏的 JSON 修好。**（至于 Godot `assets/` 下的大小写命名违规，它只发警告走 `exit 0`；Unity 和 Unreal 的资产目录故意不检查下划线命名，因为那两家本来就用 PascalCase，乱报警告只会把人逼疯。）

## 只劝不拦的 Hook，到底值不值钱

`validate-write.sh` 头部白纸黑字写着 `exit 0 always = advisory (it warns, never blocks)`。它其实干了超多活：查有没有覆盖受保护文件（`EPIC.md`、`project.godot`、引擎参考文档等）、配置枚举对不对、是不是往 `project.local.yaml` 写了锁死键、原型和正式代码有没有互相 import、本地化冻结期有没有改文案、子代理是不是越界改了不该动的文件。

它还有个挺聪明的技术细节：`Edit` 工具发给 Hook 的 JSON 里只有 `old_string` 和 `new_string`，没有改完后的完整文件。所以脚本先调 `.claude/scripts/hook-input.sh --new <tmp>` 在临时文件里模拟拼出改完后的新内容，再交给 `write-guard.sh` 检查；万一重建失败，依赖文件内容的规则会明说“没检查”，只跑依赖路径的规则，绝不拿“没跑成”冒充“检查通过”。

同样，`validate-push.sh` 盯住了往受保护分支推送以及 `git tag`、`git merge`、`gh release`、`butler push`、`steamcmd +run_app_build` 这些高风险发布动作——但它也是只告警不阻断（注释里甚至贴心地写好了“你要改成硬拦，把输出 JSON 那行换成 `echo ... >&2; exit 2` 就行”）。

## 三个踩过血坑才长出来的工程细节

读这 15 个 Hook 的源码注释，简直像在翻原作者的线上故障复盘本，有三个坑自己写 Hook 时千万别再踩一遍：

### 坑一：往 `stderr` 打印再 `exit 0`，等于对着空气拉警报

早期的写法是脚本检查到问题后，往 `stderr` 打一行警告，然后 `exit 0` 放行。结果 Claude Code 碰到 `exit 0` 时，根本不把 `stderr` 拿给用户和模型看，全塞进调试日志里了——忙活半天，两边谁都没看见。

后来统一改成调 `yaml-helper.sh` 里的 `hook_warn`，往 `stdout` 吐结构化 JSON：用 `systemMessage` 弹给用户看，用 `hookSpecificOutput.additionalContext` 塞进模型上下文，两边这才真收得到。自己给 Claude Code 写 Hook 时，第一件事一定是测通“哪条输出通道谁看得见”。

### 坑二：v1.3.0 的 Bash / PowerShell 双语多义包装（救 Windows 用户的命）

翻开 v1.3.0 的 `.claude/settings.json`，你会看到所有 15 条 Hook 命令都长得特别怪：

```text
echo `# <#` >/dev/null; bash "$CLAUDE_PROJECT_DIR/.claude/hooks/validate-read.sh"; exit $? #> ; exit 0
```

这串看似乱码的咒语，是个教科书级的 **Bash / PowerShell 双语多义（polyglot）技巧**：
- 在装了 Bash（Linux / macOS / Windows Git Bash）的机器上，`` `# <#` `` 是一次空命令替换，整行等价于老老实实运行 `bash ".../validate-read.sh"; exit $?`（后面的 `#>` 被当成注释）；
- 而在**没装 Git Bash 的 Windows 机器**上，Claude Code 会回退用 PowerShell 跑 Hook 命令。PowerShell 把 `<# ... #>` 整段识别成块注释直接跳过，只执行末尾的 `; exit 0`（`session-start.sh` 还会顺手打印一句“没找到 Git Bash，Hook 已关闭，请安装 Git for Windows”）。

以前用裸 `bash "..."` 写法时，只要 Windows 用户漏装了 Git Bash，每一次 Read、Write、Edit 和 Bash 调用都会被失败的 Hook 直接卡死，整套仓库完全没法用。改完之后，没装 Git Bash 的机器体面降级并大声告警，装了的机器行为一字节不变。

### 坑三：别在每个工具调用上白白起子进程，也别被目录名误伤

因为 `PreToolUse` 和 `PostToolUse` 会在**每一次**工具调用时触发，为了不拖慢交互，v1.3.0 给 `validate-commit.sh`、`validate-push.sh`、`validate-read.sh`、`validate-write.sh`、`validate-assets.sh`、`validate-skill-change.sh` 全部重写了纯 Bash 内建字符串匹配的快速逃生门：
- 只截取 `"tool_input"` 后面的字段做粗筛——以前匹配整个 JSON payload 时，如果你的项目放在 `~/GitHub/gamedesign/` 这种父目录里，`cwd` 和 `transcript_path` 自带 `git` 和 `design` 字样，导致**每一次**读代码和跑命令都躲不开完整解析，白白起一堆 `jq` / `awk` 子进程。
- 现在只要不沾边，纯 Bash 几毫秒直接 `exit 0` 溜走。同时每个脚本开头都按固定优先级定位项目根（当前目录有 `project.yaml` → 当前目录有 `.claude/` 且目录本身不叫 `.claude` → `CLAUDE_PROJECT_DIR` → 脚本自身相对路径），防在子目录启动时把日志写进歪树里。

## 权限层 vs Hook 层：各管一摊

`.claude/settings.json` 里的 `permissions.deny` 是宿主直接执行的硬闸门，专挡明确危险的命令（`rm -rf`、`git push --force`、`sudo`、读写 `.env`、改 `.uasset`/`.umap`）；但字符串通配符很难看懂复杂的 shell 语法。像 `validate-push.sh` 和 `validate-commit.sh` 花了近两百行 `awk` 去拆 `&&` 管道、跳过引号和 here-doc 正文、识别 `git -C "my repo"`、处理 PowerShell 单引号 here-string，就是为了干字符串匹配干不了的上下文判断。

注意一点：Claude Code 官方对 Hook 退出码和通道语义随版本偶尔会有细微调整，移植这套 Hook 时，拿你本机当前版本跑一次最小测试验证 `exit 0` / `exit 2` 谁看得见，比背文档更靠谱。

## 常见误解

- **误解一：Hook 拦住了所有违规写入。** 15 条里只有 3 处有 `exit 2`，写入前真正硬拦的只有超 40 KB 读保护和坏 JSON 提交；`validate-write.sh` 只是提醒。
- **误解二：PostToolUse 发现写坏文件可以自动回滚。** 撤不回，落盘已经发生了；`exit 2` 的价值在于强行把报错塞回模型脑子里，让它立刻自己修。
- **误解三：Hook 挂这么多，每次调工具肯定卡得要死。** 不沾边的调用在脚本开头几行就会靠纯 Bash 模式匹配秒退，不启动 `jq`、Python 或外部子进程。

## 练习

1. 如果你想把 `validate-push.sh` 对 `main` 分支的推送从“警告”改成“硬阻断”，要改哪几行？改成硬阻断后，碰到紧急 hotfix 怎么处理？
2. 解释一下 `validate-commit.sh` 为什么特意跳过普通 `cat <<EOF` 的 here-doc 正文，却**坚决不跳过** `bash <<EOF` 或 `python - <<EOF` 的 here-doc 正文？
3. 为什么 `validate-write.sh` 的快速逃生门要先剥掉项目根目录前缀，再去匹配路径里有没有 `Assets`、`Source`、`design`？

## 答案提示

1. 把告警分支里的 `hook_warn`（退出码 0）改成往 `stderr` 打印阻断原因并以 `exit 2` 退出。代价是紧急修复也会被硬拦，通常需要人工在普通终端执行，或给脚本加一条显式环境变量逃生口。
2. `cat <<EOF` 里写 `git commit` 只是文档文字或提交说明，不应该误触发检查；但 `bash <<EOF` 或 `python - <<EOF` 里的内容会真被解释器当命令执行，跳过它就成了绕过检查的漏洞。
3. 因为用户的工程完全可能放在 `C:/Source/my-game` 或 `/home/me/design-work/proj` 下；不剥掉项目根前缀，绝对路径里永远带着关键字，导致全仓库每一次无关的 Write/Edit 都逃不掉完整解析。
