# 第 07 章 产物模型：一页简报与故事、需求、ADR 三张网

## 场景：为什么模型改着改着就和设计打架了

你用 `/dev-story` 做完“近战格挡”，程序员自信满满地交差；接着 `/story-done` 接手验收，逐条对账时一把揪住第三条：“格挡成功时播放火花特效”——既没有截图，也没有运行观察记录，直接打回 `NOT ASSESSED`。

两个完全独立的技能，为什么能对着同一件事精准对账、不各说各话？靠的就是**落盘的结构化产物**。在 v1.3.0 里，CCGS 把产物体系很清醒地劈成了轻重两档：**轻量档靠一张一页简报打天下，Studio Mode 才铺开“故事 + 注册表 + ADR + 控制清单”的整套网**，而且两者中间留了平滑衔接的接口。

## 轻轨底座：一页 `design/game-brief.md`

在 `minimal` 档和 `/prototype` 主干道上，整套游戏的所有设计全压缩在 `.claude/docs/templates/game-brief.md` 这一页纸里。它不是随便写的备忘录，每个段落都有下游脚本和技能在盯着读：

- **`## In your words`**：你最初怎么描述这个游戏、回答了什么、玩完后提了什么反馈（`After play:`），一字不改原样留档，绝不准模型替你改写或总结。
- **6 个核心必填项**：`Pitch`（一句话卖点）、`Core loop`（核心循环）、`Goal & fail state`（怎么赢怎么输——后面故事的验收标准全挂在这上面）、`Features`（MVP 清单，`[ ]` 待做、`[x]` 已做、`[-]` 被 `/cut` 砍掉）、`Out of scope`（明确不做什么）、`Build order`（先做最危险、最决定好不好玩的那一步）。
- **v1.3.0 新增的三块实战字段**：`Look and references`（画面、视角、配色与参考图）、`First minute`（前 60 秒一步步怎么玩）、`Challenge`（麻烦什么时候来、输了亏什么，专门治原型太简单）；外加 `Your systems`（把你提过的每个系统标上 `in the slice` / `thin stand-in` / `later`，直接决定原型里做到多深、之后 `/create-stories` 怎么排构建顺序）、`Keep`（玩完觉得爽、死活不能改坏的东西，甚至可以用 `pins: dash_speed 14` 把 `config.js` 里的数值钉死）和 `Avoid`（明确不要的东西）。

所有标题和状态标记都强制用英文保留（正文你可以随便写中文），这样 `/cut`、`/create-stories`、`/story-done` 和 `/next-step` 的脚本才能稳定解析。每个不是你亲口说的字段都会老老实实打上 `*(guessed)*` 或 `*(provisional)*` 标签，分清哪句是你的旨意、哪句是 AI 补的空。

## 重轨骨架：故事、注册表、ADR 与控制清单

当项目从一页简报长成多系统工程，或者一上来就开了 `standard` / `full`（Studio Mode），四类产物就会彼此咬合起来。

### 1. 故事（Story）：最小可执行单元

`.claude/docs/templates/story.md` 定义了一张故事卡片的完整结构。顶部元数据直接回答“派给谁干、拿什么验收”：

```markdown
> **Epic**: [epic name]
> **Status**: [Ready | Blocked — BLOCKED: <reason>]
> **Layer**: [Foundation / Core / Feature / Presentation]
> **Type**: [Logic | Integration | Visual/Feel | UI | Config/Data]
> **Estimate**: [S | M | L]
> **Manifest Version**: [date from control-manifest.md header]
> **Last Updated**: [set by /dev-story]
```

- **`Layer`** 决定找哪个程序员（Foundation 找引擎程序，Core/Feature 按领域找玩法/AI/网络程序，Presentation 找 UI 或玩法程序）。
- **`Type`** 决定验收需要哪种硬证据（Logic 要单测、Integration 要集成测试或试玩报告、Visual/Feel 要截图加签字、UI 要截图、Config/Data 要冒烟报告）。

正文按固定顺序分成八块：`Context`（关联 GDD、TR-ID、ADR、引擎风险和控制清单规则）、`Acceptance Criteria`（验收标准）、`Implementation Notes`（从 ADR 提炼出来的实施指引）、`Out of Scope`（明确划给隔壁故事别越界）、`Files`（创建时写计划改动文件，`/dev-story` 干完后直接替换成**实际改过的文件清单**，供 `/story-done` 核对有没有乱改范围外文件）、`QA Test Cases`、`Test Evidence`、`Dependencies`。关闭故事时，`/story-done` 还会往末尾追加 `## Completion Notes` 和 v1.3.0 新增的 `## Calls beyond the design`（记录人类决定保留的 AI 自主拍板项）。

### 2. 两份注册表：不让事实在复制粘贴中腐烂

很多项目最大的噩梦是：创建故事时把设计文档里的需求抄了一份过来，三周后策划改了数值，故事里抄的那段文字成了过时化石。

CCGS 用两张中央底账挡住这个坑：
- **`docs/architecture/tr-registry.yaml`（需求注册表）**：每条需求有一个永久编号 `TR-<system>-NNN`。故事里只引用编号，模板注释写得清清楚楚：**“评审时回表读最新文本（review time read fresh）。”**
- **`design/registry/entities.yaml`（实体注册表）**：专管跨多个 GDD 的共享事实——怪物血量、掉落公式、全局常量。单份文档内部自己用的公式不必登记；一旦登记就**永不删除**（弃用只标 `status: deprecated`），改数值时注明修改日期和原因，`source` 标清唯一权威文档，所有引用方挂在 `referenced_by` 里。改一处设计时，`/propagate-design-change` 直接顺着 `referenced_by` 查出受影响的全部文档。

### 3. ADR（架构决策记录）：带版本号的摘要缓存

架构决策放在 `docs/architecture/adr-NNNN-*.md`。故事里会带三个字段：受哪份 ADR 约束（`ADR Governing Implementation`）、一两句摘要（`ADR Decision Summary`）、以及抄摘要时 ADR 的版本号（`ADR Version`，取 `Last Verified` 或 `Date`）。

这里有个很精明的省 token 玩法：**`/dev-story` 默认不让程序员去读整份长篇 ADR，而是直接把故事里的摘要内联进简报**。万一这期间 ADR 改版了怎么办？靠 `ADR Version` 比对抓包——版本号一致（或老故事没写版本号）就直接信摘要；一旦版本号对不上，立刻切去读 `references/version-mismatch.md` 处理漂移。

同时 ADR 的状态也直接卡住开工门禁：`Proposed`（还没批准）的 ADR 绝不能直接拿来写代码，必须先跑 `/architecture-decision accept ADR-NNNN`；`Deprecated` 或 `Superseded` 必须把故事改指到新 ADR 才能开工。

### 4. 控制清单（Control Manifest）：按层划红线

`docs/architecture/control-manifest.md` 按架构层（Foundation / Core / Feature / Presentation）列出“必须用什么模式、禁止用什么模式、性能红线是什么”。比如规定表现层不准直接调核心状态修改函数，必须走事件总线。单看一个孤零零的故事看不出违规，必须对照这份按层整理的清单才能抓出来。故事头部同样记着创建时的 `Manifest Version`，过期了验收时就会给你打上 `ADVISORY` 提示。

## 轻重两套产物怎么拼在一起

把整张关系网画出来，上下游一目了然：

```text
轻量线：design/game-brief.md（一页简报）
          ├─ /prototype → prototypes/<name>/ → Grow 成 Web 工程
          ├─ /cut → 砍掉的 Features 标 [-] 移入 Out of scope
          └─ /create-stories → 拆成 Story（关闭时反勾 brief 的 [x]）

重轨线（Studio Mode）：
GDD（系统设计）
  ├─ design/registry/entities.yaml（跨文档共享实体/公式）
  ├─ docs/architecture/tr-registry.yaml（权威 TR-ID 需求）
  ├─ ADR（带状态与版本的架构决策）
  │    └─ docs/architecture/control-manifest.md（按层架构红线）
  └─ Story（最小执行单元：验收标准 + 证据要求 + 实际改动文件）
        ├─ EPIC.md（史诗汇总表，关闭时同步更新状态列）
        └─ production/sprint-status.yaml（冲刺进度账本）
```

哪怕从最轻的 `/prototype` 起步，只要后来 Grow 成了 Web 工程，或者喊 `/create-stories` 开始拆故事，`/story-done` 在关闭一个故事时会顺手帮你把 `design/game-brief.md` 对应的那条 Feature 勾成 `[x]`，同步把 `EPIC.md` 里的状态列改成 `Complete`。轻重两套体系并没有割裂。

## 故事状态机：靠流程管，不靠数据库锁

故事的生命周期流转看起来像状态机：
- 初始状态：`Ready` 或 `Blocked`；
- `/dev-story` 征得你同意后改成 `In Progress`，同步改 `Last Updated` 和 `production/sprint-status.yaml`；
- `/story-done` 只有在你明确选了关闭后才改成 `Complete`，追加完成记录并同步状态账本。

但必须说句大实话：**仓库里没有任何脚本强制锁死这个状态转移**。你用编辑器直接把一个 `Ready` 故事手改成 `Complete`，不会有任何 Hook 拦你。它的状态机完全靠技能流程的纪律维系，而不是硬代码状态引擎。

## 常见误解

- **误解一：故事文件就是全部需求说明，程序员只看它就够了。** 在 `minimal` 档下确实如此；但在 `standard` / `full` 下，故事只是索引和验收清单，TR-ID 里的权威需求文本在注册表里，随时可能更新。
- **误解二：每做一个故事都得把相关 ADR 从头到尾读一遍。** 不会，默认信故事里的摘要，靠 `ADR Version` 版本戳防过期，不一致才翻原文。
- **误解三：注册表里废弃的条目可以删掉省地方。** 绝对不行。历史故事、提交记录和评审报告都挂着旧 ID，删了就会变成悬空引用，只能标 `status: deprecated`。

## 练习

1. 打开 `.claude/docs/templates/game-brief.md`，解释为什么 `Keep` 里允许写 `pins: dash_speed 14`，这行注释是给谁读的？
2. 如果某个需求 `TR-combat-001` 在故事建好两周后改了伤害公式，但没人去改故事文件里的描述，在 `full` 档下跑 `/story-done` 会按哪个版本验收？为什么？
3. 给一个“游戏暂停与音量设置菜单”写一个最小的故事头部，标出 `Layer`、`Type`，并说出它在 `minimal` 档和 `standard` 档下分别需要什么验收证据。

## 答案提示

1. `pins:` 是给 `/prototype` 迭代后的轻量自检脚本读的——用来比对 `config.js` 里你明确表示“特别喜欢、不许动”的手感参数有没有在后续修改中被意外改漂。
2. 按 `docs/architecture/tr-registry.yaml` 里的最新文本验收。因为 `/story-done` Phase 2 明确禁止信任故事里摘抄的旧文本，强制按 `id: <TR-ID>\s*$` 回注册表抓原文。
3. `Layer: Presentation`，`Type: UI`。UI 类型无论在 `minimal` 还是 `standard` 档，都必须在 `production/qa/evidence/<story-slug>/` 留存实际运行后的页面截图（UI 故事不需要单元测试，也不需要额外的视觉签字文档）。
