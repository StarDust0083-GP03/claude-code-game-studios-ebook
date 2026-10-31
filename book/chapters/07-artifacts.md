# 第 07 章 产物模型：故事、需求、ADR 三张网

## 场景

`/dev-story` 选中一个故事，读了它的验收标准，开始写代码。半小时后它报告完成。`/story-done` 接手，逐条核对验收标准，发现第三条"格挡成功时播放火花特效"既没有截图，也没有运行记录，于是标成 UNTESTED，判决停在 NOT ASSESSED。

这两个技能之所以能对同一份内容做出可比较的判断，是因为它们读的是同一种产物：故事文件。这一章讲清三类核心产物如何互相咬合。

## 故事：最小可执行单元

`.claude/docs/templates/story.md` 定义了故事的全部字段。头部是元数据：

```markdown
> **Epic**: [epic name]
> **Status**: [Ready | Blocked — BLOCKED: <reason>]
> **Layer**: [Foundation / Core / Feature / Presentation]
> **Type**: [Logic | Integration | Visual/Feel | UI | Config/Data]
> **Estimate**: [S | M | L]
> **Manifest Version**: [date from control-manifest.md header]
> **Last Updated**: [set by /dev-story]
```

`Layer` 决定派给哪个程序员：Foundation 给引擎程序员，Core 和 Feature 按类型分，Presentation 给 UI 或玩法。`Type` 决定需要什么证据：Logic 要单元测试，Integration 要集成测试或试玩记录，Visual/Feel 要截图加签字，UI 要截图，Config/Data 要冒烟报告。

这两个字段合起来就是"谁做、怎么算做完"。

正文分八节：

- Context：指向 GDD 文件、需求 ID、ADR、引擎与风险、控制清单规则。
- Acceptance Criteria：从 GDD 摘出的、属于这个故事的验收条件。
- Implementation Notes：从 ADR 的实施指南提炼的具体指示，程序员读这一段而不是读整份 ADR。
- Out of Scope：由邻近故事负责的内容，明确不在此实现。
- Files：计划改动的代码和测试文件，`/dev-story` 结束时替换成实际清单。
- QA Test Cases：QA 主管写的测试用例，开发者照着实现，不得自行发明。
- Test Evidence：所需证据的类型和路径。
- Dependencies：依赖哪些故事，解锁哪些故事。

有一句注释很关键：需求文本的权威位置是 `docs/architecture/tr-registry.yaml`，故事里引用的版本可能在评审时已经过时，所以"review time read fresh"。

## 需求注册表：事实的唯一出处

`docs/architecture/tr-registry.yaml` 存的是一条条编号需求，形如 `TR-combat-001`。故事引用 ID，评审时按 ID 回表读最新文本。

这解决了一个常见问题：故事创建时抄了一份需求描述，三周后设计改了，故事里的文字变成了化石。用 ID 引用，文本只有一份。

同一个模式出现在 `design/registry/entities.yaml`，存的是跨文档的游戏世界事实：实体、物品、公式、常量。文件头规定了写入规则：

- 只登记跨系统边界的事实，单份 GDD 内部使用的公式不必登记。
- 永不删除条目，用 `status: deprecated` 标记。
- 值改变时更新值、写修改日期，并注释旧值和哪份 GDD 改的。
- `source` 是权威 GDD，其他引用它的文档列在 `referenced_by`。
- 新 GDD 引用已有条目时，追加路径，不新建重复条目。

文件顶部还列了读取方和搜索模式，比如"所有实体名"用 `^  - name:`，某个 GDD 拥有什么用 `source: design/gdd/combat.md`，某个 GDD 引用了什么用路径加 `-B 8`。

这些搜索模式不是给模型自由发挥的，而是给 `.claude/scripts/registry.sh` 的固定读法。第 11 章会展开。

## ADR：决策的时间戳

架构决策记录（ADR）放在 `docs/architecture/`，编号 `ADR-NNNN`。故事里引用三个字段：

- `ADR Governing Implementation`：哪一份 ADR 管这个实现。
- `ADR Decision Summary`：一两句话的决策摘要。
- `ADR Version`：ADR 的 `Last Verified` 日期，没有就用 `Date`，都没有就写 `unversioned`。

`/dev-story` 的规则是：版本相同、故事没有版本字段、或双方都是 `unversioned` 时，信任故事的摘要；版本不同时，才去读 ADR 并处理版本冲突。

注意这里的工作量分配：程序员默认不读整份 ADR，只读故事里的摘要。这样省上下文，代价是摘要可能失真。仓库用版本号来检测失真，而不是每次重读。

ADR 的状态也参与门禁。`Proposed` 状态的 ADR 不能作为实施依据，必须先用 `/architecture-decision accept ADR-NNNN` 转为 Accepted。`Deprecated` 或 `Superseded` 状态会要求把故事指向继任者。

## 控制清单：跨故事的架构约束

`docs/architecture/control-manifest.md` 是一份按层组织的规则清单，每层列出必须遵守的模式、禁止的模式、性能护栏。故事头部记录它创建时的清单版本。

版本不一致时，`/dev-story` 会读一个版本冲突处理文件；`/story-done` 则把"故事写在旧版清单上"记为 ADVISORY，建议跑 `/story-readiness` 检查。

这是三张网里最容易被忽略的一张。它管的是"这个架构里不允许出现什么"，比如某个层不能用直接引用，必须走事件总线。单看一个故事不会发现违规，只有对照清单才能判断。

## 三张网如何咬合

把三类产物放在一起看，关系是：

```
GDD（设计事实）
  ├─ 需求注册表（可引用的需求 ID）
  ├─ ADR（决策 + 版本）
  │    └─ 控制清单（按层的约束）
  └─ 故事（验收标准 + 证据要求 + 文件范围）
        └─ 冲刺计划（排序与容量）
```

故事是最小的执行单元，向上引用事实，向下产生证据。评审技能不需要重读全部设计，只需要顺着故事里的引用回表。

这个结构的代价是前期投入。standard 档位下，写第一行代码前会有 30 份文档。作者自己的对照实验显示，这些文档带来的是可追溯性，而不是更好的游戏。理解这一点，你就知道该在什么规模的项目上用哪一档。

## 状态机

故事状态没有单独的状态机文件，它由几个约束共同维护：

- 模板允许的初始状态是 `Ready` 或 `Blocked`。
- `/dev-story` 在开始时把状态设为 `In Progress`，`Last Updated` 写今天。
- `/story-done` 只在用户明确选择关闭时把状态设为 `Complete`，并追加完成记录。
- `production/sprint-status.yaml` 同步维护 `status: in-progress` / `done` 和顶层 `updated` 日期。

没有任何脚本强制这些转换。一个故事可以从 Ready 直接跳到 Complete，只要有人手动改。状态机的强制力来自技能流程，而不是代码。

## 常见误解

误解一：故事文件是任务的完整规格。它是一份索引加验收标准，权威事实在设计文档和注册表里。

误解二：ADR 每次实施都要读。默认读故事里的摘要，版本不一致时才回原文。

误解三：注册表可以随便删条目。文件头明确禁止删除，只能标废弃。因为历史故事和评审记录会引用旧 ID。

## 练习

1. 打开故事模板，找出三个直接决定"派给谁"和"需要什么证据"的字段。
2. 假设一个需求文本在故事创建后被修改，说明评审时会读到哪个版本，依据是什么。
3. 为一个"设置菜单"功能写一个最小故事头部，标注 Layer、Type 和所需证据。

## 答案提示

1. `Layer` 决定程序员角色，`Type` 决定证据类型，`Status` 决定能否开始。`Manifest Version` 影响版本冲突检查。
2. 评审读注册表里的最新文本，因为故事只存 ID，并且模板注释要求评审时回表读取。
3. 例如 Layer: Presentation，Type: UI，证据是一张或多张截图放在 `production/qa/evidence/<story-slug>/`，不需要单元测试。
