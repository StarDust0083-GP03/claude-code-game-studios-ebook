# 第 04 章 配置求值：一个 rigor 如何长出六个设置

## 场景

你在 `project.yaml` 里只写了一行：

```yaml
modes:
  rigor: standard
```

然后在技能里看到 `workflow: standard`、`qa.level: standard`、`review_mode: lean`、`team.size: individual`、`docs.density: balanced`、`story_granularity: balanced`。六个值你一个都没写。

到 `project.local.yaml` 里写 `modes.review_mode: solo`，自己的会话立刻从 lean 切到 solo，而不影响团队里其他人。再删掉 `project.yaml` 里的 rigor，所有值回落到 minimal 展开。

这套行为集中在 `.claude/hooks/yaml-helper.sh` 的 `resolve_setting` 函数里。它是全仓库被调用次数最多的逻辑，理解它就理解了技能的"环境"。

## 解析链

`resolve_setting` 按固定顺序查五个来源，第一个给出合法值的就是答案：

1. `project.local.yaml`，仅当该键在"本地可覆盖"白名单里。
2. `project.yaml`。
3. 旧版纯文本镜像，例如 `production/review-mode.txt`、`production/stage.txt`。
4. rigor 展开。
5. 文档化的末端默认值。

![配置解析链：第一个合法值胜出，非法枚举继续下落](../../wiki/assets/diagrams/config-chain.svg)

每一级都有两个动作：读到值后先做枚举校验，非法值丢弃并继续往下走，而不是让一个拼错的值污染所有技能。最终输出两列，值和来源。

在快照仓库上直接调用，输出是：

```
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
testing.strict: logic=unset integration=unset visual=unset ui=unset config=unset (unset = each skill applies its own default)
performance.enforce: warn (default)
platform.cert_tier: (unset -- ask which platforms are in scope)
system_overrides: none
notes: none
```

括号里的来源比数值有用。`rigor: minimal (default)` 说明项目没配过，`review_mode: solo (rigor:minimal)` 说明它来自展开而不是显式设置。排查"为什么技能行为不对"时，先看来源。

## 展开表

`yaml-helper.sh` 里有一张三行表，把 rigor 翻译成六个键：

```
minimal :: modes.workflow=minimal, docs.density=terse, qa.level=minimal,
           modes.story_granularity=coarse, modes.review_mode=solo, team.size=individual
standard:: modes.workflow=standard, docs.density=balanced, qa.level=standard,
           modes.story_granularity=balanced, modes.review_mode=lean, team.size=individual
full    :: modes.workflow=full, docs.density=thorough, qa.level=full,
           modes.story_granularity=fine, modes.review_mode=full, team.size=studio
```

展开位置很关键：它在所有显式来源之后、末端默认之前。因此显式写了 `docs.density: terse` 的项目，行为与引入 rigor 之前完全一致。这也是向后兼容的保证。

`modes.workflow` 有点特殊。它有一个按系统覆盖的机制 `workflow_overrides.system_overrides`，可以只把战斗系统提到 full，其余保持 minimal。解析时先看系统覆盖，再看 `modes.workflow`，最后才是 rigor 展开。

## 为什么要一条链，而不是一个配置文件

设想三种真实需求。

团队共享的规范：引擎、命名、性能预算。这属于项目，应该进版本控制。`project.yaml` 承担这一层。

个人偏好：我习惯 solo 评审，我的机器上下文小，不想每次等四个总监。这属于开发者，不该污染团队配置。`project.local.yaml` 承担这一层，同时被 gitignore。

历史遗留：旧版本把评审模式写在 `production/review-mode.txt`，把阶段写在 `production/stage.txt`。已经升级的项目里这些文件还在。镜像文件承担这一层，但优先级低于 YAML。

三种需求冲突时，顺序就是答案：个人高于项目，项目高于遗留，遗留高于展开，展开高于默认。

## 读白名单与写白名单必须同步

`yaml-helper.sh` 里有一段注释值得抄进任何配置系统：

> 这个列表必须等于 `/settings --local` 的写入白名单。如果解析时查询 `project.local.yaml` 的范围比 `/settings` 能写的范围窄，那么一次 `/settings --local modes.review_mode=solo` 会成功写入、成功显示，然后被每个技能忽略。

这不是理论问题，是"写列表和读列表不一致"这类 bug 的典型症状：配置看起来生效了，实际没有。仓库的应对方式是把两个列表放在同一处，并在测试里断言它们同步。

当前可本地覆盖的是 `modes.review_mode` 和 `team.size`。理由是这两个是个人工作习惯，其余设置影响团队产物的一致性。

## 失败模式

文档列了一张失败清单，每一条都对应一种真实的坏输入：

- `project.yaml` 不存在：走遗留文件和默认，备注 `project.yaml absent`。
- 文件存在但为空：备注 `project.yaml is EMPTY`，与不存在区分开。被截断的写入会表现成这个状态。
- YAML 格式错误：解析失败的键留空，继续往下走。
- 用了 Tab 缩进：拒绝，并在备注里给出**行号**。
- CRLF 换行：正常解析，照顾 Windows 默认。
- UTF-8 BOM：正常解析，BOM 不会污染第一个键。
- 键存在但值为空：视为未设置，继续往下，不会解析成空字符串。
- 枚举值非法：继续往下，并在备注里点名被拒绝的值。
- 重复键或重复块：块合并，重复键取最后一个值，并在备注里列出两处行号。

最后一条值得单独说。多数 YAML 工具遇到重复块只保留最后一个，这里选择合并，因为两个 `modes:` 块同时出现时，用户通常是想补充而不是覆盖。合并比丢数据安全。

还有一类输入不产生备注：形状错误。比如 `rigor:` 下面跟了一个列表而不是标量，键会解析为空，回落到默认，且不会告诉你。文档明确承认这个盲区，并给出排查方法：当某个设置看起来被忽略时，检查它的键是不是一行一个标量。

## 技能里怎么用

技能正文开头通常有一行：

```
!`bash "${CLAUDE_SKILL_DIR}/../../hooks/yaml-helper.sh" resolve_config --keys automation,workflow,qa.level,gate_level,engine_values,specialists,perf_budgets,system_overrides`
```

`!` 前缀让 Claude Code 在把正文交给模型之前执行这条命令，把输出注入上下文。之后的正文写着"Resolved above, use as-is"。模型不需要自己读 YAML、拼路径、处理优先级。

这条设计把"确定性计算"从模型手里拿走了。代价是 `allowed-tools` 必须精确授予这条命令，否则整次技能调用会因为缺少授权而中止。仓库在 `config-resolution.md` 里专门写了授权格式，并区分了"预批准"和"准入控制"：`allowed-tools` 只是免去权限提示，并不限制其他命令；而未授权的注入命令会让技能直接失败。

## 常见误解

误解一：`project.yaml` 写什么就生效什么。旧版镜像文件、非法枚举、本地覆盖都可能改变结果。要用 `resolve_config` 看最终值和来源。

误解二：`rigor` 是总开关，改它一定全变。被显式钉住的键不受影响，这正是那六个键的意义。

误解三：`project.local.yaml` 能覆盖任何设置。只有白名单里的两个键可以，其余会被忽略并在备注里点名。

## 练习

1. 在副本里把 `modes.rigor` 设为 `full`，运行 `resolve_config`，记录六个派生值。
2. 再把 `modes.workflow` 显式设为 `minimal`，重新运行，观察哪些值变了，哪些没变。
3. 构造一个 Tab 缩进的 `project.yaml`，看备注如何报告行号；再构造一个 `rigor` 下面跟列表的文件，解释为什么没有备注。

## 答案提示

1. 应得到 workflow=full、docs.density=thorough、qa.level=full、story_granularity=fine、review_mode=full、team.size=studio，来源全部标 `rigor:full`。
2. workflow 固定为 minimal（来源 `project.yaml`），其余五个仍从 rigor 展开，来源 `rigor:full`。
3. Tab 缩进会得到带行号的备注；列表形状会被解析为空值并回落到默认，脚本无法区分"故意的空值"和"写错了形状"，因此不报备注。排查时手动检查键的形状。
