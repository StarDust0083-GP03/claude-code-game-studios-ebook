# 第 11 章 注册表：跨文档事实如何不漂移

## 场景

三份设计文档都提到哥布林。战斗文档说它有 12 点生命，经济文档说掉落 3 枚金币，任务文档说它是"精英怪"。三周后战斗文档把生命改成 18，另外两份没动。等到实现时，程序员按哪份写？

这类问题靠人工同步必然漂移。CCGS 的答案是把跨文档事实集中到注册表，其他文档引用而不是复制。

## 三个注册表

仓库里有三份：

`design/registry/entities.yaml` 存游戏世界事实：实体、物品、公式、常量。文件头的规则很具体：

- 只登记跨系统边界的事实。单份 GDD 内部使用的公式不必登记。
- 永不删除条目，用 `status: deprecated` 标记。
- 值改变时更新值、写修改日期，并注释旧值和哪份 GDD 改的。
- `source` 是权威 GDD，其他引用它的文档列在 `referenced_by`。
- 新文档引用已有条目时追加路径，不新建重复条目。

`docs/architecture/tr-registry.yaml` 存需求条目，编号 `TR-<system>-NNN`。故事引用 ID，评审时回表读最新文本。

`docs/registry/architecture.yaml` 存架构层面的状态、契约、系统、目标帧率、用途、模式。它是控制清单和架构评审的共同底稿。

## 一个脚本，三种读法

`.claude/scripts/registry.sh` 把三份注册表统一成一种读法。子命令有九个：

- `list`：每个条目一行，可加 `--system` 只留某个系统的需求。
- `get`：按名字取条目及其原始行。
- `refs`：给名字返回它引用的路径，给需求 ID 返回引用它的故事或史诗，给路径返回所有引用该路径的条目。
- `slice`：某个文件作为 source 或 gdd 或 adr 涉及的全部条目。
- `validate`：重复名、故事引用了不存在的需求、路径不存在、状态越界、布局不支持。
- `compare`：比较变更前后的注册表，列出被删除的条目和新增的非法状态。
- `next-id`：给出下一号。

在快照上跑 `validate`：

```
registry	entities	design/registry/entities.yaml	0
registry	tr	docs/architecture/tr-registry.yaml	0
registry	architecture	docs/registry/architecture.yaml	0
checked	production/epics	0
duplicate	0
tr_unknown	0
path_missing	0
status	0
layout	0
```

三份注册表都能读，条目数为 0，五个检查项都是 0。输出是 TSV，每行第一列是类别。脚本注释写明：它只输出观察，不输出判决。缺一个路径重不重要、故事能不能引用已废弃的需求，由调用技能决定。

`next-id` 的行为也实测过：

```
$ bash .claude/scripts/registry.sh next-id story stealth
next	story	stealth	story-001	-	0
```

格式是 `next <kind> <scope> <id> <highest> <count>`。最高号是 `-`，已见 ID 数为 0，所以下一号是 `story-001`。

## 为什么 ID 只增不减

`next-id` 的规则是"见过的最大号加一"，不是"找最小空号"。脚本注释说明：删除或废弃过的 ID 永远不再发放。

这条规则看起来浪费编号，实际是审计需要。旧故事、旧评审、旧提交信息里都引用过 `TR-combat-007`。如果这个号被回收给另一条需求，历史记录会指向错误的对象，而且无法察觉。

`compare` 子命令也基于同样的假设：注册表是只追加的。它列出"旧表有、新表没有"的条目，因为正常变更不该删除条目。

## 布局为什么这么严格

注册表是 YAML，但读取方式不是通用 YAML 解析器，而是一套固定布局规则：

- 一个 section 是第 0 列的一个键，持有块列表；空时写 `[]`。
- 一个条目以 `- name: <name>` 开头，短横线在第 0 列或第 2 列，同一 section 内必须一致。
- 字段比短横线深两列，更深的行属于上一个字段。
- 含 `": "` 的值必须加引号。
- `|` 或 `>` 开头的是多行文本，比键更深的行都属于它。

任何不符的行都报 `LAYOUT`，附行号和期望的写法，并且该注册表的条目全部不读，而不是猜。

为什么要放弃通用解析器？脚本头部给了一个理由：`bash 3.2` 和 `BWK awk` 兼容，无 Python 依赖。macOS 自带 bash 3.2，这个限制是真实的。用固定布局换取零依赖，代价是写错格式时条目会整份失效。

失效被设计成显式的。`LAYOUT` 行会明确告诉你哪一行不符合，而不是安静地少读几条。这就是 `skill-authoring.md` 第二条义务的实践：缺失值不能默认成宽松解释。

## 兼容旧格式

脚本里有一个刻意的例外：架构注册表里早期版本写过 `status: superseded_by: ADR-NNNN`，没有给值加引号。

严格按布局规则，这一行会被判为不支持。脚本选择读它，把状态读成 `superseded_by: ADR-NNNN`，同时输出一行 `UNQUOTED`，告诉你在哪一行、应该写成什么样。

这个处理方式值得借鉴：对历史数据宽容读取，但把不规范之处明确报出来，让用户有机会修。既不因为一个旧格式让整份注册表失效，也不假装它完全合规。

## 读取者清单

`entities.yaml` 的文件头列了谁会读它，以及每条读法的 Grep 模式：

```
WRITTEN BY: /design-system, /consistency-check, economy-designer, systems-designer
READ BY:    /design-system, /consistency-check, /review-all-gdds, /design-review,
            /content-audit, /balance-check, /propagate-design-change, /asset-spec, ...
```

这份清单的价值在于变更影响分析。要改注册表格式，先看谁在读；要新增一个读取方，先确认它的读法与现有布局兼容。

`/propagate-design-change` 的读取方式特别有意思：它用 `referenced_by` 找出所有引用某个事实的文档，然后逐个评估影响。这是把"改一处要同步多处"从人的记忆变成了图遍历。

## 常见误解

误解一：注册表是给人看的文档。它主要是给脚本和技能读的，人只是维护者。

误解二：可以随时清理无用条目。只能标废弃，因为历史引用仍然有效。

误解三：格式错了脚本会猜。它会报 `LAYOUT` 并跳过整份注册表，避免基于半个文件做判断。

## 练习

1. 在副本里给 `entities.yaml` 加一个条目，字段缩进故意写错两格，运行 `registry.sh validate`，观察输出。
2. 用 `registry.sh refs` 查询某个 GDD 路径，说明输出中 `how` 列可能出现哪些值。
3. 解释为什么 `next-id` 不回收已删除的编号，并用一个具体场景说明回收的后果。

## 答案提示

1. 会得到 `LAYOUT` 行，带文件、行号、发现的和期望的布局，该注册表条目数为 0。
2. `source`、`gdd`、`adr`、`referenced_by`，以及 `cited`（故事或史诗引用某个需求）。
3. 假设 `TR-combat-007` 被删除后回收给了 `TR-ui-007`，旧故事仍写着 `TR-combat-007`，评审回表会读到完全不同的需求，而且没有任何报错。只增不减可以避免这种静默错配。
