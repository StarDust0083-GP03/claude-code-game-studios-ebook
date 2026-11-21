# 第 11 章 注册表：跨文档事实怎么管才不漂移

## 场景：一只哥布林，三份文档写出三种血量

项目做了一个月，三份文档都提到了哥布林：战斗 GDD 写它 12 点血，经济 GDD 写它掉 3 个金币，任务 GDD 顺口写了句“12 血的精英怪”。两周后策划把哥布林调成 18 血，只改了战斗 GDD，另外两份没人记得动。等程序和 QA 进场，每个人看到的都是不同版本的真相。

靠人肉“记得同步改三处”肯定要翻车。CCGS 的办法很朴素：**凡是跨文档共享的硬事实，全部收进中央注册表；其他文档只准引用编号或名字，不准各自抄一遍。**

## 三张底账，各记各的

仓库里一共三份 YAML 注册表：

1. **`design/registry/entities.yaml`（游戏世界底账）**：存跨系统的实体、物品、公式、全局常量。文件头把纪律写得很清楚——单份 GDD 内部自己玩的小公式不用登记；一旦登记**永不删除**（废弃标 `status: deprecated`）；改数值要留日期和修改原因注释；`source` 指明唯一权威 GDD，其他用到它的文档全挂在 `referenced_by` 列表里，绝不另起重复条目。
2. **`docs/architecture/tr-registry.yaml`（需求底账）**：按 `TR-<system>-NNN` 编号存权威技术需求。故事里只挂 ID，写代码和验收时回表查最新需求原文。
3. **`docs/registry/architecture.yaml`（架构底账）**：记系统分层、契约、目标帧率和 ADR 状态，是控制清单和架构评审的共同数据源。

## 一个脚本统一三张表：`.claude/scripts/registry.sh`

为了不让 75 个技能各自拿五花八门的 `grep` 去啃 YAML，所有读写核验全部收敛到 `.claude/scripts/registry.sh` 里，提供一组干净的子命令：

- `list`：按行摊开条目（可用 `--system` 过滤单个系统）；
- `get`：按名字抓出完整条目和原始行；
- `refs`：反向查图——给实体名查谁引用它，给 TR-ID 查哪些故事/史诗挂了它，给文档路径查所有指向它的条目；
- `slice`：拉出某份 GDD 或 ADR 牵扯到的全部条目；
- `validate`：全套体检——查重名、故事引用了不存在的 TR-ID、指向的文件路径丢了、状态值越界、缩进布局不对；
- `compare`：比对改动前后的两份注册表，专抓“谁偷偷删了老条目”或“写进了非法状态”（`validate-registry.sh` Hook 背后调的就是它）；
- `next-id`：发下一个可用编号。

在空白模板仓里跑一遍 `bash .claude/scripts/registry.sh validate`，吐出整洁的 TSV 事实行：

```text
registry        entities        design/registry/entities.yaml         0
registry        tr              docs/architecture/tr-registry.yaml    0
registry        architecture    docs/registry/architecture.yaml       0
checked         production/epics        0
duplicate       0
tr_unknown      0
path_missing    0
status          0
layout          0
```

跑 `bash .claude/scripts/registry.sh next-id story stealth`，返回：

```text
next    story   stealth story-001       -       0
```

注意它依然死守那条规矩：**只吐事实，不判生死**。路径丢了算不算阻断、故事引用废弃需求该不该打回，全交回给上层技能结合当前档位去定。

## 为什么编号永远只增不减，绝不回收

`next-id` 的算法不是“从 1 开始找第一个空号”，而是**“把见过的所有编号里最大的找出来加 1”**。就算 `story-002` 到 `story-006` 全被你删了，只要见过 `story-007`，下一个发出去的铁定是 `story-008`。

看起来编号会变得坑坑洼洼，但这是审计底线：以前的 git 提交信息、废弃故事、旧评审报告里早就写死了 `TR-combat-007`。要是把 007 回收再发给一条新需求，历史记录就会悄无声息地指鹿为马，连脚本都抓不出来。同样的道理，注册表本身是**只追加不删除**的，`validate-registry.sh` 只要发现你在 Write/Edit 里把老条目删了或改了编号，立刻拉响警告。

## 为什么宁可定死缩进规矩，也不用通用 YAML 库

点开 `registry.sh` 的源码，你会发现它压根没引 PyYAML，甚至不依赖 Python，而是拿 **Bash 3.2 + BWK awk** 硬解析。为了做到 macOS 自带老 Bash 也能零依赖直接跑，它立了一套严格的 `# LAYOUT:` 布局契约（还印在了三份注册表文件头里）：

- 分组键顶格写在第 0 列，空列表写 `[]`；
- 每个条目以 `- name: <name>`（或对应主键）开头，短横线在第 0 列或第 2 列，同一分组必须对齐；
- 字段比短横线缩进两格；
- 值里只要带了 `": "`（冒号加空格），必须用引号包起来；
- `|` / `>` 开头的块文本，缩进更深的行归它。

最狠的一条错误处理是：**只要碰上一行不符合布局规矩，脚本直接吐 `LAYOUT` 报错（带行号和正确写法），并且整份注册表一条都不读，绝不硬猜。**

为什么不“凑合把能读的先读出来”？因为凑合读出半张表，上层做一致性检查时就会基于残缺数据给你判个“没有冲突”，比直接报错危险十倍。宁可大声罢工，绝不静默丢数据。

## 对老版本历史脏数据的优雅宽容

死板归死板，碰到自家老版本留下的历史债，它的处理特别老道。v1.1.3 的 `/architecture-decision` 曾经在 `docs/registry/architecture.yaml` 里把被取代的状态写成：

```yaml
status: superseded_by: ADR-NNNN
```

没加引号，里面冒出两个冒号，按严格 YAML 和布局规矩都是非法的。如果一刀切整表拒读，所有升级上来的老项目当场瘫痪；如果默默吞掉，老毛病永远没人修。

`registry.sh` 的折中办法是：**宽容读进来（正常解析状态），但同时吐一行 `UNQUOTED` 点名哪一行该补上引号**。老项目升级完照样能干活，又能按图索骥把历史债还清。

## 谁写、谁读，直接贴在文件脑门上

翻开 `design/registry/entities.yaml` 的文件头注释，你会看到一块像接口文档一样的“消费者声明”：

```text
WRITTEN BY: /design-system, /consistency-check, economy-designer, systems-designer
READ BY:    /design-system, /consistency-check, /review-all-gdds, /design-review,
            /content-audit, /balance-check, /propagate-design-change, /asset-spec, ...
```

甚至把每种常用查询对应的正则都贴在旁边。以后你想改注册表字段结构时，扫一眼文件头就知道会牵连哪几个技能；而 `/propagate-design-change` 干脆把“策划改了一个数值要通知谁”这件事，从靠人脑记变成了顺着 `referenced_by` 做图遍历。

## 常见误解

- **误解一：注册表主要是给人当策划百科看。** 错，它首先是给脚本和技能机读的结构化底账，人只是维护和审批它的。
- **误解二：需求砍掉了，直接把对应的 `TR-` 条目从文件里删干净更清爽。** 绝对不行，必须留着并标 `status: deprecated`，否则历史引用全变悬空，还会触发 `validate-registry.sh` 警告。
- **误解三：YAML 格式写歪了两格没关系，脚本会自动纠偏。** 不会。`registry.sh` 撞到不合规缩进直接报 `LAYOUT` 并放弃读取整张表，逼你修干净。

## 练习

1. 如果你在 `design/registry/entities.yaml` 里手写了一条新实体，不小心把字段缩进多敲了两格，跑 `registry.sh validate` 会看到什么现象？为什么说“读出 0 条”比“跳过出错的那一条继续读”更安全？
2. 用 `registry.sh refs` 查一份战斗 GDD 的路径时，可能会看到哪些关系类型？这些关系对 `/propagate-design-change` 有什么用？
3. 假设你正在把这套注册表机制抄到自己的后端微服务项目里，用来管跨服务的错误码或事件名，你会把哪些规则照搬过去、哪些可以简化？

## 答案提示

1. 会吐出带具体行号和期望格式的 `LAYOUT` 报错行，并且把该注册表的读取计数置为 0。如果跳过坏行继续读，上层的重名检查和引用检查就会在缺了一块事实的前提下报“无冲突”，造成危险的假通过。
2. 可能出现 `source`（权威来源）、`gdd`、`adr`、`referenced_by`（被动引用）以及 `cited`（被故事/史诗引用）。`/propagate-design-change` 正是靠这些边找出“改了这份文档必须同步评审哪些下游文档和故事”。
3. “编号只增不减、废弃不删、集中脚本统一读写与校验、坏格式显式报错不瞎猜”这四条完全值得照搬；如果你的团队环境本来就有固定的 Python/Node 运行时，可以把手写 awk 布局解析换成标准 YAML/JSON Schema 校验，省掉手写缩进限制的维护成本。
