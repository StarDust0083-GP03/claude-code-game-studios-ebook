# 第 13 章 引擎与品类适配：统一引擎表、Web 一等公民与品类库

## 场景：为什么把代码写进 `src/` 在 Unity 里比报错更可怕

同一条 `/dev-story` 命令，跑在不同引擎的项目里，代码该往哪落盘完全不同：
- Godot 4 / Web：`src/`
- Unity：`Assets/`
- Unreal Engine 5：`Source/<Module>/`

最阴的地方在于**写错了不会报错**。Unity 编译器只认 `Assets/` 和 `Packages/`，把 C# 脚本写进 `src/`，文件安安静静躺在那儿，编辑器里压根看不见；测试写进 `tests/` 更要命，Unity 测试运行器直接给你弹一行绿油油的 **`0 tests, Passed`**——看起来全绿，其实一条都没跑。

到了 v1.3.0，CCGS 在适配层做了三大升级：把散落各处的引擎路径和命令收进了统一总表 **`.claude/engines/engines.tsv`**、把 **Web（Vite + TypeScript + Three.js / Phaser / PixiJS）** 正式拉进四大引擎一等公民、还新增了 **`.claude/genres/` 73 份品类知识库**，彻底把“引擎怎么配、品类怎么问”从散落的提示词变成了结构化数据。

## 一张总表管四大引擎：`.claude/engines/engines.tsv`

打开 `.claude/engines/engines.tsv`，一共只有 5 行（1 行表头 + 4 行引擎），用 Tab 分隔，空槽统一写 `-`（防止 Bash 按 `IFS` 读的时候把空列吞掉）：

| `engine` | `code_root` | `test_root` | `asset_root` | 默认 `run` / `build` / `test` / `smoke` 命令 |
|---|---|---|---|---|
| **Godot** | `src` | `tests` | `assets` | 自带窗口运行、gdUnit4 无头测试和 `--quit-after 5` 冒烟 |
| **Unity** | `Assets` | `Assets/Tests` | `Assets` | 均为 `-`（依赖编辑器路径和目标，由 `/setup-engine` 填） |
| **Unreal** | `Source` | `Source/<Module>/Private/Tests` | `Content` | 均为 `-`（同上） |
| **Web** | `src` | `tests` | `assets` | `npm run dev` / `npm run build` / `npm test` / `npm run smoke` |

所有 Hook 和辅助脚本全部通过同一个小解析器 **`.claude/scripts/engine-row.awk`** 读这张表，技能则通过 `resolve_config --keys engine_row` 直接拿算好的一整行。

不过源码文档 `.claude/engines/README.md` 也很实诚地留了一笔例外：**`test-scaffold.sh` 目前没读这张表**，它自己写死了各引擎的测试路径，所以如果你魔改了 `engines.tsv` 里的 `test_root`，得记得去 `test-scaffold.sh` 同步改一处。

## 五步代码根解析：填错了也不准偷偷回退

有了总表之后，`.claude/docs/code-root-resolution.md` 和 `yaml-helper.sh` 里的 `resolve_code_root()` 把代码根解析定成了五步（v1.3.0 新增第 0 步自定义目录）：

0. **读 `project.yaml` 的 `engine.code_root`（仅限项目配置，不认 `project.local.yaml`）**：专门照顾非标准目录（比如 Godot 项目把代码放在 `scripts/`，或者一个扁平网页小游戏直接填 `.` 把根目录当代码根）。
   - 填 `.` 时，辅助函数 `code_root_filter` / `code_root_find` 会自动把 `.claude`、`.git`、`production`、`design`、`docs`、`tests`、`studio-tests`、`prototypes`、`tools`、`node_modules`、`dist` 这些框架和产物目录全剔出去，绝不误扫。
   - **最狠的一条规矩**：如果 `engine.code_root` 填了个不能用的值——目录压根不存在、大小写拼错、带 `..`、写了绝对路径、或者指向了 `docs`/`.claude` 这类框架目录——脚本直接把它判成 **`invalid`**（`code-markers.sh` 甚至直接返回 `exit 3`），**绝不偷偷回退到引擎默认目录**！不然你把 `scripts` 拼成了 `scritps`，脚本默默回退去扫一个空着的 `src/`，最后给你报个“零违规”，比直接报错危险得多。
1. **读 `engine.name`**（查 `engines.tsv` 对应行）。
2. **读旧版镜像**（`.claude/docs/technical-preferences.md` 里的 `Engine:` 行，占位符 `[TO BE CONFIGURED]` 不算）。
3. **目录树无歧义推断**：当且仅当 `src/`、`Assets/`、`Source/` 里**恰好只存在一个**时才认它；同时出现两个就不猜。这里还藏着一个跨平台暗坑——Windows 和默认 macOS 文件系统不区分大小写，直接用 `[ -d Assets ]` 去测，Godot 项目里的小写 `assets/` 也会命中，导致 `src/` + `assets/` 被误判成“歧义”。所以必须按真实目录列表精确比对大小写。
4. **其余所有情况：判成 `unresolved`（未解析），绝不默认回落 `src/`**。

拿到 `unresolved` 或 `invalid` 后，行动原则极其干净：
- **所有读取和扫描**（安全审计、硬编码检查、本地化扫描、内容盘点）：一律报 `NOT ASSESSED — code root unresolved/invalid`，绝不吐出“零命中”冒充干干净净。
- **所有写入**：直接停手不写，报错让人先把代码根配对。

## Web 成为一等公民：脚手架、锁死版本与无专属 Agent

v1.3.0 把 `Web` 拉进一等公民后，设计得很克制，没有盲目再造 5 个 Web 子代理，而是靠三块实在东西落地：

1. **脚手架与起步模板（`.claude/engines/web/`）**：新项目跑 `/setup-engine` 没指定引擎时，现在**优先推荐 Web**，只问你一个问题：要纯原生（Canvas 2D + Web Audio），还是加 Three.js、Phaser、PixiJS？选完由 `web-scaffold.sh` 拷出完整配置（绝不覆盖已有文件），直接配齐 `npm run dev`、`npm run build`、`npm run build:single`（单文件打包）、`npm test`（Vitest + Playwright）和 `npm run smoke`；如果你手里早就有个 Web 工程，`web-detect.sh` 会原样登记，一根文件都不乱动。
2. **版本钉死参考（`docs/engine-reference/web/VERSION.md`）**：跟三大重引擎一样，Web 也有自己的版本对照表和破坏性变更手册。v1.3.0 的脚手架锁死了 **Vite 8.3.4（Rolldown/Oxc 取代 Rollup/esbuild）、TypeScript 7.0.2（原生编译器）、Vitest 5.0.5、Playwright 1.64.1、Three.js 0.186.1、Phaser 4.2.1、PixiJS 8.22.0**（要求 Node `^22.12 || ^24 || >=26`），并且 `/prototype` 里的 3D 打包脚本 `vendor-three.sh` 用的是同一版 Three.js 0.186.1，确保原型 Grow 成正式 Web 工程时不会撞上版本断层。
3. **复用通用程序员**：Web 没有单独的引擎专家角色，`/dev-story` 做引擎检查时直接让 `lead-programmer` 对照 `docs/engine-reference/web/` 审核代码。

## 引擎知识快照：同时防“模型太旧”和“本机太旧”

`docs/engine-reference/<engine>/` 专门对冲大模型知识截止日期（文档里统一把 May 2025 标成下限，新版模型可能知道得更多，但一律先查本目录），每个引擎下面放 `VERSION.md`、`breaking-changes.md`、`deprecated-apis.md`、`current-best-practices.md` 和按子系统拆的速查卡（每份控制在 150 行内）。

v1.3.0 的两个实操细节值得留意：
- **修掉了两处真实的 Godot 4.7 勘误（#143）**：旧文档误写 4.6 起 Windows 默认渲染器换成了 Direct3D 12、还教代理把 `Compositor` 当子节点挂上去；v1.3.0 更正为 Windows 默认仍是 Vulkan，`Compositor` 是挂在 `WorldEnvironment` 或 `Camera3D` 的 `compositor` 属性上的资源。
- **双向缺口意识**：不只是“模型训练数据太旧、不知道新 API”（正向缺口），还有**反向缺口**——比如参考文档已经写到 Godot 4.7 或 Phaser 4，但你本机老项目装的其实是 Godot 4.4 或 Phaser 3，代理照着新参考写出来的 API 在你机器上直接编不过。所以每份 `VERSION.md` 都醒目地提醒先核对 `Installed at pin time` 或锁文件里本机真实装的版本，绝不盲信模板里的钉死版本。

## 品类知识库（`.claude/genres/`）：让 AI 问出内行问题

v1.3.0 新增了一整个 **`.claude/genres/` 目录（实测 73 个文件）**，专门给 `/prototype` 供血：

- **`chipsets.yaml` + `chipsets/` 下 69 份品类卡片**：涵盖平台跳跃、类银河战士恶魔城、肉鸽卡牌、塔防、幸存者、农场模拟、城市建造、战棋、解谜等主流品类。每张卡写清四件事：塑造这个品类的关键分岔问题（Choices）、手感变体（Feel variants）、前 60 秒默认该有的核心要素（Card defaults & Feel，战斗类品类甚至在 `chipsets.yaml` 里标了第一关敌人种类的底线 `variety: {enemies: 3|4}` 防止做出来只有一种换皮怪）、以及哪些重功能坚决留到后面做（Later，并标清对应哪一步：`change it after play` / `grow it` / `add it as a feature` / `needs a server`）。
- **`mashups.md`**：教 `/prototype` 遇到“两个品类混搭”（比如宝可梦 + 自走棋）时，按“输入与镜头、死亡与存档、成长与经济、核心规则”四个系统拆分谁当老大，避免两套规则打架。
- **`art-direction.md`**：帮没指定画风的用户给出贴合品类的具体视觉方案（配色角色、轮廓、标志性细节），专门治 AI 默认只会画“米色背景 + 光秃秃圆块”的通病。
- **`online-and-devices.md`**：遇到联机、VR、手机触控、主机需求时，怎么在本地浏览器里找合理替代品顶着，并把真需要服务器或真机测试的部分诚实划进 `Out of scope`。
- **`sources.md`**：列出卡片引用过的公开设计资料与说明书出处。

更讨喜的是 `chipsets.yaml` 文件头那句大实话：**“每一条品类归类和敌人种类底线都是基于经典作品读出来的假设，不是科学实测数字，且从不把整张品类表当菜单甩给用户挑。”** 拿它当提问脚手架很管用，拿它当圣经就跑偏了。

## 常见误解

- **误解一：只要在 `project.yaml` 设好 `engine.name: Godot`，就能区分 GDScript 和 C#。** 区分不了。`engine.name` 只定引擎和目录，语言专家要看 `specialists.code`（`godot-gdscript-specialist` vs `godot-csharp-specialist`）。
- **误解二：`engine.code_root` 填错了没事，框架会自动回退去扫 `src/`。** 绝对不会。v1.3.0 专门把非法自定义根设计成硬报错 `invalid`，因为静默回退去扫错目录只会产出致命的“零违规”假通过。
- **误解三：`.claude/genres/` 里的 73 个文件每次开会话都会灌进上下文。** 不会。连原型构建阶段都不加载 `chipsets.yaml`，只在 `/prototype` 提问出简报那一瞬读一次索引，再按需打开命中的那 1–2 张品类卡片。

## 练习

1. 如果你的老 Unity 项目同时有一个空着的 `src/` 目录和真实的 `Assets/` 目录，但你还没配置 `project.yaml`，跑 `resolve_code_root()` 会返回什么？如果强行往 `project.yaml` 写 `engine.code_root: assets`（小写），在大小写敏感和不敏感系统上分别会怎么处理？
2. 为什么 `.claude/engines/engines.tsv` 要求每个空单元格都必须填 `-`，而不能留空？
3. 假设你想给自己的非游戏项目（比如 Web 后端模板）抄一套类似 `.claude/genres/` 的“场景知识库”，你会怎么设计索引文件和单场景卡片，才能既让 AI 问出内行问题，又不把上下文撑爆？

## 答案提示

1. 同时存在 `src/` 和 `Assets/` 且未设引擎属于歧义，会返回 `unresolved` 并拒绝猜测；而在 `project.yaml` 里把实际叫 `Assets` 的目录写成小写 `assets`，按 `code-root-resolution.md` 的大小写实名比对规则会被直接判为 `invalid`，不回退，提示你修正拼写。
2. 因为 Bash 的 `IFS=$'\t' read` 会把连续的 Tab 折叠成一个分隔符，导致后面的列全部错位；写死 `-` 占位再配合 `awk -F'\t'` 读取，列号永远不会漂。
3. 照抄两级按需加载：用一个轻量索引（如 `archetypes.yaml`，只放类型名、一句话定义、语义匹配词）定位 1–2 个场景（比如“CRUD 管理后台”、“定时 ETL 管道”、“高并发 Webhook 网关”），再只打开对应的单页卡片——里面写 5–8 个带默认值的分岔问题、必踩坑清单和明确留到后期做的项，构建时只看产出的一页简报，不再背整套知识库。
