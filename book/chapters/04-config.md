# 第 04 章 配置求值：一个 `rigor` 如何长出六个设置

## 场景：少写配置，为什么反而更稳

你在 `project.yaml` 里其实只写了两行：

```yaml
modes:
  rigor: standard
```

可等技能跑起来，上下文里自动冒出了六个清清楚楚的值：`workflow: standard`、`qa.level: standard`、`review_mode: lean`、`team.size: individual`、`docs.density: balanced`、`story_granularity: balanced`。

接着你在被 `.gitignore` 忽略的 `project.local.yaml` 里加了一句 `modes.review_mode: solo`。你自己的会话瞬间省掉了多总监评审，团队里其他人一点不受影响。万一哪天手滑把 `modes.rigor` 拼成了 `strict`，整套流程也没炸，而是悄悄回落到 `minimal`，还在 `notes` 里把你拼错的词点名拎出来。

这套把“简单入口、团队规范、个人习惯、老版本兼容、脏数据兜底”全捏在一起的求值器，全写在 `.claude/hooks/yaml-helper.sh` 里，配套的读写技能在 v1.3.0 里正式改名叫 **`/project-settings`**（老名字 `/settings` 保留为转发层）。它是全仓库被调得最勤的一块代码。

## 五级瀑布解析链

调用 `resolve_setting <key>` 时，脚本不看心情，死板地沿着五级瀑布往下走，**谁先给出一个合法值，谁就赢**：

1. **`project.local.yaml`**：前提是这个键在“本地可覆盖”白名单里，不在白名单的直接跳过。
2. **`project.yaml`**：团队共享的显式配置。
3. **旧版纯文本镜像**：兼容老版本留下的 `production/review-mode.txt`、`production/stage.txt`。
4. **`rigor` 展开**：把 `modes.rigor` 映射成 6 个子开关。
5. **末端默认值**：什么都没配时的保底值（比如 `rigor=minimal`、`automation=collaborative`）。

![配置解析链：第一个合法值胜出，非法枚举继续下落](../../wiki/assets/diagrams/config-chain.svg)

每经过一级，脚本都要把读到的值拿去核对 `_yaml_helper_enums`（v1.3.0 共收了 **26 个** 枚举与布尔键，包含新增的 `engine.name::Godot|Unity|Unreal|Web` 和 `project.goal` 的 9 个合法目标）。**如果值非法，直接丢弃并记进备注，继续往下跌落**——绝不拿一个拼错的值污染全仓技能，也绝不因为一个拼写错误直接把会话崩掉。

在刚克隆的空仓库上跑 `bash .claude/hooks/yaml-helper.sh resolve_config`，你会看到类似这样的输出：

```text
=== CCGS Resolved Config ===
rigor: minimal (default)
review_mode: solo (rigor:minimal)
automation: collaborative (default)
workflow: minimal (rigor:minimal)
docs.density: terse (rigor:minimal)
story_granularity: coarse (rigor:minimal)
qa.level: minimal (rigor:minimal)
team.size: individual (rigor:minimal)
project.stage: not set (unset)
automation_always_ask: scope_changes, file_deletions, schema_changes (default)
engine: unset (fall back to .claude/docs/technical-preferences.md)
testing.strict: logic=unset integration=unset visual=unset ui=unset config=unset ...
performance.enforce: warn (default)
platform.cert_tier: (unset -- ask which platforms are in scope)
system_overrides: none
notes: none
```

排查“技能怎么没按我想的跑”时，**括号里的来源比前面的值更有用**。看到 `(default)` 说明没配过，看到 `(rigor:minimal)` 说明是被总档位展开的，看到 `(project.yaml)` 说明被显式钉死了。

## `rigor` 展开表与“显式值压过展开”

`yaml-helper.sh` 里写死的三行展开表很直白：

| `modes.rigor` | `workflow` | `docs.density` | `qa.level` | `story_granularity` | `review_mode` | `team.size` |
|---|---|---|---|---|---|---|
| `minimal` | `minimal` | `terse` | `minimal` | `coarse` | `solo` | `individual` |
| `standard` | `standard` | `balanced` | `standard` | `balanced` | `lean` | `individual` |
| `full` | `full` | `thorough` | `full` | `fine` | `full` | `studio` |

因为展开排在第 4 级（在显式配置之后、默认值之前），你可以非常灵活地做混搭：比如整仓 `rigor: full`，但单独在 `project.yaml` 里把 `docs.density: terse` 钉死，就能拿到“严谨验收但文档精简”的组合。

另外 `modes.workflow` 还挂了一个单系统逃生口：`workflow_overrides.system_overrides`。整个项目都可以跑 `minimal`，只把战斗系统拉到 `full`。解析单个故事时，先看它所属系统有没有覆盖，没有再退回项目级 `workflow`。

这也反过来解释了第 03 章的坑：**如果手痒把 6 个子开关的默认值抄进了 `project.yaml`，以后再改 `modes.rigor` 就全白搭**，因为第 2 级显式值永远压在第 4 级展开头顶上。

## 个人白名单：哪些能本地改，哪些被锁死

团队一起开发时，有两类配置不能混：
- **影响磁盘产物的配置必须锁在 `project.yaml`**（比如 `engine.name`、`engine.code_root`、`modes.rigor`、`modes.workflow`、`qa.level`、`project.goal`）。不然张三按 `full` 建了一堆 ADR，李四本地切 `minimal` 跳过了，仓库产物立马分裂。
- **只影响个人体验的偏好允许放 `project.local.yaml`**。

翻开 `.claude/hooks/yaml-helper.sh` 第 596 行，`_yaml_helper_locally_overridable` 白名单里一共列了 **15 个键**：
- `rigor` 展开族里的 2 个：`modes.review_mode`、`team.size`；
- 交互与严格度开关：`modes.automation`、`modes.automation_always_ask`、`testing.strict.{logic,integration,visual,ui,config}`、`performance.enforce`；
- 功能与提醒开关：`features.session_state`、`features.token_budget_warn_at`、`features.read_guard`、`features.read_guard_kb`、`updates.check`。

这里藏着配置系统最常犯的一类 bug：**写校验的白名单和读解析的白名单分家**。要是 `/project-settings --local` 允许你把一个键写进 `project.local.yaml`，而 `resolve_setting` 读的时候压根不查它，就会出现“写入成功、查询显示、实际全仓无视”的灵异事件。

CCGS 的处理很干脆：把白名单集中放在 `yaml-helper.sh` 这一处，`/project-settings` 直接调它的 `is_locally_overridable`；针对手改 `project.local.yaml` 的情况，还专门补了 `validate_local_scope` 函数——只要你在本地文件里手写了锁死键（比如把 `modes.rigor` 塞进本地文件），开会话时立刻点名警告“这个键不能本地覆盖，已被忽略，请挪去 `project.yaml`”，绝不静默吞掉。

还有一个很细的防呆设计：`/project-settings` 在写入前还会做两道额外检查：
1. **拼写检查（`config-set.sh --dry-run`）**：如果你打了个框架压根不认的键名，它会拦下来并给出拼写最接近的合法键名让你确认。
2. **保留键警告（Reserved-setting detection）**：文档里有些已经占位但目前还没任何技能去读的键，`/project-settings` 不硬写死名单，而是动态 `grep` 查 `.claude/docs/effects-map.md` 里的 `> ### RESERVED` 标题。无论你是查全部、查单个还是写配置，撞上了都会明明白白告诉你“这个值我帮你存下来了，但目前没有任何技能读它，改了也不生效”。

## 脏数据兜底：生产级 Bash/Python 解析器踩过的坑

`yaml-helper.sh` 里藏着大量一看就知道踩过真坑的防御代码，值得自己写配置解析器时照着检查一遍：

- **布尔值也必须放进枚举表**：以前 `testing.strict.logic` 没进枚举表，有人在本地误写成 `maybe`，结果把 `project.yaml` 里的 `true` 给盖掉了，而 `/story-done` 只认字面量 `true` 才阻断，一个拼写错误悄悄把硬门禁降级成了口头提醒。所以现在所有布尔键全进了 `_yaml_helper_enums`；而且 `features.session_state` 专门枚举成 `on|off`（不是 `true|false`），因为写 `false` 会被当成非 `off` 从而继续开启！
- **多行文本块（`|` / `>`）绝不当成配置键**：有人在 `notes: |` 里写了一行注释 `review_mode: full`，旧解析器真把它当配置读进去了。v1.2.0 之后专门加了 `block_indent` 跳过块标量内部所有缩进行。
- **Tab 缩进报错带行号**：YAML 规范本来就禁 Tab，以前只剥空格导致 Tab 缩进行直接隐身，所有枚举校验还绿灯通过——等于拿一份全空配置冒充校验合格。现在专门扫描并报出 Tab 所在行号。
- **重复块合并并点名**：如果文件里不小心出现了两个 `modes:` 块，普通 YAML 库往往直接用后一个盖死前一个；这里选择把两个块合并（同名叶子取后者），同时在 `validate_yaml_enum` 里报出重复键的行号提醒你清理。
- **一次启动 Python 解析全表**：早期 `validate_yaml_enum` 为 23 个枚举键各起一次 Python，在 Windows 上每次冷启动 200 多毫秒，两个文件一跑就是将近 10 秒，直接把 `session-start.sh` 干超时了。后来改成只起一次 Python 读完文件回答所有枚举，耗时变成常数。
- **不往上爬父目录找 `project.yaml`**：曾经实现过“当前目录没有就往上找父目录”，结果删掉了。因为如果你的小项目嵌套在另一个带 `project.yaml` 的大仓库下面，往上爬会悄悄吃到外层项目的配置，还把“有 `project.local.yaml` 却缺 `project.yaml` 必须报错”的规则给搞哑火了。现在只认当前目录和 `CLAUDE_PROJECT_DIR`。
- **已知盲区**：如果你把一个标量键写成了列表（比如 `rigor:` 下面跟 `- full`），解析器拿不到标量就会当成空值回落到默认，且不会吐备注。碰到配置神秘失效时，第一反应是检查它的值是不是一行标量。

## 技能里的 `!` 注入：别让模型自己算配置

打开几乎任何一条 `SKILL.md`，正文第一行都是这样：

```bash
!`bash "${CLAUDE_SKILL_DIR}/../../hooks/yaml-helper.sh" resolve_config --keys automation,workflow,qa.level,...`
```

这个感叹号让 Claude Code 在把提示词交给模型**之前**，先在 shell 里把脚本跑完，把算好的结果直接贴在正文最上面。紧接着一句“Resolved above — use as-is”，模型彻底不用自己找文件、算优先级、猜默认值。

不过这招有个前提：命令必须跟 `allowed-tools`（或 v1.3.0 放进 `settings.json` 的全局 `allow`）严丝合缝匹配，哪怕多包一层 `cd ... &&` 都可能因为没命中白名单直接卡住。所以 `/project-settings` 里反复叮嘱模型：跑 `yaml-helper.sh` 时老老实实敲单条裸命令，别画蛇添足。

## 常见误解

- **误解一：`project.yaml` 里写什么，技能就一定按什么跑。** 错。本地覆盖、旧版 txt 镜像、非法枚举下落、单系统覆盖都可能改写结果。以 `resolve_config` 或 `/project-settings` 打出来的最终值和来源为准。
- **误解二：`project.local.yaml` 只能覆盖 `review_mode` 和 `team.size`。** 那只是 `rigor` 展开族里的 2 个；完整白名单其实有 15 个个人体验键（包括 `modes.automation`、`testing.strict.*`、`features.read_guard`、`updates.check` 等）。
- **误解三：`locked` 意思是这辈子都改不了。** 不是。`/project-settings` 里标 `locked` 只代表“不能在 `project.local.yaml` 里个人覆盖”，团队依然可以用 `/project-settings <key>=<value>` 写进 `project.yaml` 覆盖 `rigor` 展开。

## 练习

1. 如果你在 `project.yaml` 里同时写了 `modes.rigor: full` 和 `docs.density: terse`，再用 `/project-settings modes.rigor=minimal` 把档位降下来，`docs.density` 和 `qa.level` 分别会变成什么值？来源分别显示什么？
2. 为什么 `yaml-helper.sh` 专门把 `testing.strict.logic` 这类布尔开关也放进枚举校验表，而不放行任意字符串？
3. 假设你手里有两个嵌套仓库：外层 `/work/project.yaml` 写了 `rigor: full`，内层 `/work/mini-game/` 只有老版本的 `production/review-mode.txt`。如果在内层目录跑配置解析，为什么绝不能“向上递归寻找 `project.yaml`”？

## 答案提示

1. `docs.density` 保持 `terse`（来源 `project.yaml`，显式钉住的值压过 `rigor` 展开）；`qa.level` 跟着降成 `minimal`（来源 `rigor:minimal`）。
2. 因为下游技能（如 `/story-done`）通常按字面量 `true` 判断是否阻断；如果不校验枚举，本地误填一个 `maybe` 就会压过项目里的 `true`，在零报错的情况下把硬门禁悄悄降成建议级。
3. 一旦向上递归，内层目录会偷偷读到外层的 `project.yaml`（甚至外层的 `project.local.yaml`），直接把内层自己的遗留配置和默认行为顶掉，属于最难查的静默串味故障。
