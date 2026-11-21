# 第 03 章 入门：先玩一把（`/prototype`）与 Studio Mode（`/start`）双轨入口

## 为什么 v1.3.0 把入口掉了个头

按 v1.2.0 的老路子，你克隆完仓库敲 `/start`，它会先带你盘仓库、推算流程强度、写 `project.yaml`，然后指引你先 `/setup-engine`、再 `/brainstorm`、再 `/create-stories`、最后才到 `/dev-story` 写第一行代码。这套路逻辑很严密，但对刚克隆模板、脑子里刚蹦出一个游戏点子的人来说，**前半小时都在填表、选引擎、批文档，连个会动的画面都没见着**。

v1.3.0 彻底拧转了这个顺序：**只要项目还没绑定重引擎（Godot / Unity / Unreal），默认主干道就是“先做个浏览器里双击能玩的原型”**——也就是 **"Make me a game"**，入口是 `/prototype`；而 `/start` 成了双轨总控台，第一选项直接把你送进 `/prototype`，只有当你确实在做多人合作、长周期或者需要全套文档追溯的项目时，才带你进 **Studio Mode**。

这章把这两条入口轨道从源码里彻底拆清楚。

## 轨道一：`/prototype` 一把搓出可玩原型（主干道）

直接敲 `/prototype 一个稀有鱼只在黄昏咬钩的钓鱼游戏`（或者在对话里直说“帮我做个游戏”），只要没设置非 Web 引擎、也没传 `--path engine|paper`，`SKILL.md` 里的路由表不会多问一句，直接进 **One-shot 流水线（One-shot 1 → 5）**。

### 第一步：最多问一轮（约 8 题），写一页 `game-brief.md`

这步的逻辑全写在 `.claude/skills/prototype/references/one-shot-1-card.md` 里，专门治“需求太糊，做出来的原型像玩具”：

1. **先匹配品类，绝不甩菜单**。它读一遍 `.claude/genres/chipsets.yaml`，按语义把你描述的游戏匹配到一个或多个品类（比如“像宝可梦但自动战斗”会同时命中 `creature-collector` 和 `auto-battler`），只打开命中的品类卡片（`.claude/genres/chipsets/<name>.md`），混搭游戏再顺手读 `mashups.md` 决定每个系统由谁主导。
2. **点子太糊先给 2–3 个一句话提案**。如果你只说了“做个赛车游戏”甚至“随便做个游戏”，它先给你 2–3 个一句话 pitch（干什么、怎么输、长什么样、什么手感）。你全否决（“都不喜欢，太慢了，不要射击”），它会把你嫌弃的点原封不动记进 `Avoid`，再换 2–3 个新提案。
3. **只问一轮，全带默认值**。从品类卡的“塑造玩法的关键选择”、“手感变体”、“画面方向（来自 `art-direction.md`，支持直接贴图或往 `references/` 丢参考图和 `notes.md`）”、“挑战何时到来与失败代价”、“目标”里挑出你话里没说清的，合并成**一条消息里最多约 8 个问题**，每个问题标好 `(usual)` 默认值。你可以随便跳、只答两条，或者干脆回一句“你帮我选（you pick）”。**绝没有第二轮追问**，没答的全按默认值填，并在简报里标成 `*(provisional)*`（你自己没被问到、它替你猜的标 `*(guessed)*`）。
4. **最后一题顺手切分“切片 vs 单机制快测”**。如果你其实只想试一下“抓钩手感”，它会直接拐进 Spike Mode（`/prototype --spike`），连简报都不写。
5. **抄袭拦截与平台降级**。如果你喊着“照抄一个一模一样的 Pac-Man”，它绝不直接照抄，而是先问你要“同品类原创”还是“加自己扭转的新变体”，并把原作名字、美术、角色和 UI 写进 `Avoid`；如果你提了联机、VR、手机或主机，它会查 `online-and-devices.md`，用一句话直白告诉你本地浏览器先拿什么替代方案顶着，把服务器/联网记进 `Out of scope`。

聊完这一轮，它照着 `.claude/docs/templates/game-brief.md` 亮出一页简报——**整份简报就是确认卡**。它刻意保留一个叫 `## In your words` 的区，把你的原话一字不改粘进去，后面所有改动都得跟它对账；除了 6 个核心必填项（Pitch、Core loop、Goal & fail state、Features、Out of scope、Build order），还硬补上了老简报最缺的三块：**Look and references（画面与参考）**、**First minute（前 60 秒玩什么）**、**Challenge（挑战从哪来，绝不能简单到闭眼赢）**，以及拆解颗粒度用的 `Your systems`（标记哪些 `in the slice` 真做、哪些 `thin stand-in` 做薄桩、哪些 `later` 以后再说）。

简报下面还会贴出本次构建的开销与落盘清单（注意：它先跑 `printenv CLAUDE_CODE_EFFORT_LEVEL` 看环境变量有没有锁死推理档位，绝不凭空编造预计耗时和费用），等你点下 **Build it** 才动手写文件。

### 第二步：当前会话搓原型 + 无头浏览器 5 分钟小检查

点完 Build it，除非你明确点了“build it at medium”之类要降档省钱的指令，否则它**直接在你当前主会话里开写**（不额外起子代理），产物落在 `prototypes/<name>/`，基于 `.claude/docs/templates/one-shot-lean/` 起步：

- 双击 `index.html` 就能在浏览器里直接开玩；
- 禁止拿 emoji 糊弄美术，也禁止只画几个光秃秃的圆点；
- 所有数值参数必须集中进 `config.js`，方便后面挂滑块调参。

写完先不急着交差，必须过 `one-shot-2c-self-check.md` 的**约 5 分钟冒烟检查**。这里有个很清醒的克制：**不写 AI 自动玩游戏的机器人，也不准写脚本自己调难度**——好不好玩、难不难，必须真人玩了算。脚本只管四件硬事：

1. **boots**：调 `one-shot-check.sh prototypes/<name> --keys "..."`，用无头浏览器（Chrome / Edge / Chromium）按几下真实游戏按键，确认零报错、零崩溃、零 `NaN`/`Infinity`、非白屏，且按键对比无输入确实有响应。
2. **shot**：把运行截图 `evidence/play.png` 打开肉眼对着简报看；检查文字有没有跑出屏幕、小于 14px、对比度低于 3:1 或互相重叠，检查画面有没有卡死。
3. **brief words**：核对 `evidence/brief-words.tsv`（你原话里的每个画面/视角关键词怎么落地的）和 `evidence/nearest-game.txt`。
4. **emoji and outlines**：扫描代码确保零 emoji，再用 `page-shot.sh ... --query scene=figures` 拍一张 `evidence/figures.png`，确认每种敌人和单位都有各自独立的轮廓。

此外还要跑 `one-shot-check.sh --checklist`，把简报里每一条 Feature、前 60 秒、挑战和系统逐一写进 `evidence/checklist.tsv`（标 `pass` / `missing` / `broken` / `not_assessed`，每条 `pass` 必须指到截图或代码行号，声音和手感这类看不出来的直接标 `not_assessed`）。出问题最多只给**一轮修复机会**，修完重跑，还坏着的必须如实列在交接卡的 `Still broken:` 里，脚本直接拒绝第三轮刷分。

最后交给你的交接卡末尾硬钉着一句：**"Not yet played by a person"**，并询问是否提交和打上 `one-shot/<name>` 标签——这是你以后随时能回滚的锚点。

### 第三步：玩完改、挂滑块、分享，以及 Grow 成正式工程

玩完之后，这条线才显出工程味：

- **口语微调（One-shot 4）**：直接说“跳得太低了”或“太简单了”。每次改动前先对照简报的 `Keep` / `Avoid` / `Out of scope`；如果你说“太简单”或“每波都一样”，规则要求**先加至少一条提升压力或给新选择的新机制，再动数值**；改完只跑轻量检查（不重跑整套小检查），你满意就打成一个 `iteration N: <what>` 提交，随时能说“回到 iteration 2”。
- **按需挂滑块调参**：你喊要自己调手感时，它才把 `tune.js` 加进来（按反引号或加 `?tune` 呼出，自动给 `config.js` 每个值配滑块），你调完点 Save 复制参数块粘回对话，`one-shot-tune.sh` 自动写回 `config.js` 并记进 `feel-log.md`。
- **导出分享与导入老游戏**：喊分享时 `one-shot-share.sh` 剥掉调参面板和工作文件生成干净的 `prototypes/<name>/dist/`；如果手里早就有个网页小游戏，用 `/prototype --from <path>`（或 `/start` 自动探测）原封不动按字节拷进 `prototypes/<name>/`，打上 `baseline/<name>` 标签并反写一份简报，之后就能走同一套迭代和成长流程。
- **Grow 成正式 Web 工程（One-shot 5）**：你玩爽了给出 `PROCEED`，它会只问一个问题：“继续当原型改，还是长成正式 Web 工程？”选 Grow 之后，先过 `one-shot-grow.sh guard`（检查 Node ≥ 22.12、工作区干净、根目录没撞名的 `index.html`），然后分五步每步独立提交，把单文件原型变成根目录的 **Vite + TypeScript + Vitest + Playwright** 项目，数值迁进 `data/config.json`，并且**用同一颗随机种子和同一串按键输入在拷贝前、拷贝后、转 TypeScript 后各回放一次（`one-shot-grow.sh replay`）**，拿 `match yes` 证明重构没有改坏哪怕一点行为，最后打上 `grown/<name>` 标签，原始 `prototypes/<name>/` 一根汗毛不动。
- **长完之后一次聊一个功能，想收尾喊 `/cut`**：不用急着写史诗和冲刺计划，直接报下一个想加的功能，做完自动跑 `npm run smoke` 和同种子回放；直到你主动想进 Studio Mode，或者故事/功能超过 9 个时 `/next-step` 提醒你一次。临近发布可以跑 `/cut`（读取简报与测试记录，绝不建议砍 `Keep` 里的内容，商业目标 `sell` / `early_access` / `publisher` 还会按 70% 时间进度帮你算建议冻结日）。

## 轨道二：`/start` 如何扫描仓库、切进 Studio Mode

如果你不知道从哪开始、手里已有设计文档或老代码，或者本来就想走正规多角色工程流，就敲 `/start`。

### 先用脚本摸底，绝不靠模型瞎猜

`/start` 启动后先静默跑一遍 `bash .claude/scripts/project-state.sh`（除非你的第一句话本身就在要一个游戏——这时它会用 Skill 工具直接转交给 `/prototype`）。在刚克隆下来的空白 v1.3.0 仓库上，脚本吐出来的三列 TSV 事实表长这样（字段名、值、来源）：

```text
root            /path/to/ccgs     -
engine          -                 unset
code_root       src               detected
source_files    0                 src
concept         -                 absent
systems_index   -                 absent
gdd_files       0                 design/gdd/*.md
adr             0                 docs/architecture/adr-*.md
story           0                 production/epics/**/story-*.md
prototype       0                 prototypes/*/
sprint          0                 production/sprints/*.md
milestone       0                 production/milestones/*.md
origin_url      https://github.com/Donchitos/Claude-Code-Game-Studios.git  .git/config
stage_yaml      -                 project.yaml
stage_txt       -                 absent
stage           -                 unset
phase           -                 unset
phase_inferred  concept           nothing
```

看这张表时，**第三列（来源）比第二列（值）更要命**，`/start` 对它立了四条硬规矩：

1. `source_files` 为 `unknown` 时必须说“代码根没解析出来”，绝不准说成“没有代码”。
2. `origin_url` 只要包含 `donchitos/claude-code-game-studios`，就得提醒你 `origin` 还指着上游模板仓库，别一激动把提交推上去，建议先 `git remote rename origin template` 再挂自己的远程。
3. **`phase_inferred` 明确要求忽略**。脚本自己算了一个按文件数猜出来的阶段，但 `/start` 正文直白禁止使用它——因为一个写了一堆代码、没写过设计文档的老项目，根本不是“进入了 Production 阶段”，宁可按规则判定，也别拿假聪明的猜测替掉事实。
4. 如果你已经在 `project.yaml` 里设了引擎且有了概念文档/简报，`/start` 直接判定你是老用户，报一句当前状态后让你去敲 `/next-step`，不浪费时间重走引导。

### 四选一分流与三项推断卡片

摸完底，`/start` 只问一个问题：“你现在处在什么起点？”

- **A）Make me a game（浏览器可玩原型）**：如果没定非 Web 引擎，直接跳过写配置卡片，让你敲 `/prototype` 开始（未写 `rigor` 本来就按 `minimal` 算）。
- **B）有个模糊点子，或者啥也没有**：没定引擎时依然优先推荐直接 `/prototype` 先出提案和原型，也可走 `/brainstorm`。
- **C）清晰概念**：可以马上 `/prototype`、先 `/brainstorm` 写下来，或者直接 `/setup-engine`。
- **D）已有作品**：v1.3.0 这里藏着个贴心细节——它会先用 Glob/Grep 扫两层目录，看有没有你从别处放进来的现成 HTML 网页游戏（带 `<script>` 且含 `<canvas>` 或 `requestAnimationFrame`，且不是带 `package.json` 的 Node 工程），找到了直接给 `/prototype --from <path>`；如果发现你有 GDD 设计文档却一个可玩原型都没有，没定非 Web 引擎时还会建议先拿你的概念文档跑一遍 `/prototype`，把文档先变成能玩的东西。

如果你的回答和扫描结果打架（比如仓库里明明有代码你却选了 B），它会指出来再问你一次。

走 B/C/D 进规划线后，`/start` 会根据你说的话和磁盘文件数，一次性推算出三个值（不再连环追问）：

- **Stage（阶段）**：无 GDD 是 `Concept`，有 GDD 无 ADR 是 `Systems Design`，有 ADR 是 `Technical Setup`。
- **Rigor（流程强度）**：撞上“开放世界、RPG、模拟、沙盒、派系、经济、MMO、多人、很多系统”推 `full`；撞上“发布、商业、Steam、清晰核心循环”或已有 9 份以上系统 GDD 推 `standard`；撞上“Game Jam、周末、原型、小游戏、练手”或没命中任何关键词，统统回落 `minimal`。
- **Goal（目标，v1.3.0 新增 `project.goal`）**：从你的原话里猜 `jam` / `learn` / `hobby` / `portfolio` / `sell` / `early_access` / `publisher` / `mobile` / `other` 之一（商业类目标优先级压过兴趣类，`early_access` 和 `publisher` 压过 `sell`），以后 `/cut` 会读这个字段决定要不要帮你设发布冻结日。

算完后亮一张假设卡片，只给三个选项：**Save them / Change something / Don't save**。同意保存时，它**只通过脚本写四个字段**：`project.stage`（同步镜像 `production/stage.txt`）、`project.goal`、`modes.rigor` 和下一步问出来的 `modes.automation`。

**它死活不替你把 `modes.workflow`、`modes.review_mode`、`team.size` 等 6 个子开关写进 `project.yaml`**——原因下一章细讲，因为只要显式写死进去，以后你改 `modes.rigor` 就再也拧不动它们了。

### 最后一行：为什么让你自己敲命令，不替你跑

除了开场第一句话就直接要游戏（需要立刻跳去 `/prototype` 且不占用 `/start` 的 Sonnet 模型）这一个例外，`/start` 结束时只打印干巴巴的一行：

`Type /prototype to begin.`（或者 `Type /setup-engine to begin.`）

哪怕你刚点完“好，就从这个开始”，它也**坚决不代你启动下一个技能**。源码里把原因写得很透：`/start` 自己钉在 `model: sonnet` 上，如果由它代调下一步，新技能会吃不到你主会话的模型，而且让用户亲手敲命令，等于由人显式接过权限和预期，不搞暗度陈仓的自动连锁。

顺便提醒一句：以后走到半路忘了下一步该干嘛，直接敲 **`/next-step`**（v1.2.0 叫 `/help`）。在 `minimal` 档下它甚至不走 7 阶段目录，而是直接调 `story-status.sh` 或看 `prototypes/` 与 `grow-*/replay.args`，永远只给你指**当下唯一该干的一件事**，绝不甩一大堆菜单糊你脸上。

## 常见误解

- **误解一：用 `/prototype` 就等于放弃了整套工程规范。** 并不是。One-shot 照样有 1 页结构化简报、集中调参的 `config.js`、无头浏览器自检、Git 标签回滚，还能平滑 Grow 成带 Vitest + Playwright 和同种子回放的 TypeScript 工程；只是省掉了写第一行代码前那 29 份前置文档。
- **误解二：`project-state.sh` 输出 `code_root: src` 说明项目已经配好了 Godot。** 盯紧第三列：`detected` 只是“目录里碰巧只有一个候选文件夹”的推断，并不是 `engine.name` 配置出来的。
- **误解三：敲了 `/help` 会报错。** 不会。v1.3.0 保留了 `.claude/skills/help/SKILL.md` 作为 20 行的兼容转发层，会打印一行 `/help is now /next-step. Running /next-step.` 然后自动转交；但新配置和日常习惯直接用 `/next-step` 就好。

## 练习

1. 如果你手里没配引擎，先跑了一把 `/prototype` 做完一个塔防游戏，之后突然想改用 Unity 重做，按 `prototype/SKILL.md` 和 `one-shot-5-grow.md` 的规则，框架会帮你把 JS 代码转成 C# 吗？为什么？
2. 假设你在 `/start` 里选了 C（清晰概念），原话是“想做一个准备上 Steam 抢先体验的像素肉鸽，先当周末小项目练练手”，按 Phase 4 的两张信号表，推断出的 `rigor` 和 `project.goal` 分别是什么？
3. 为什么 `/start` 明明能把 `modes.rigor` 展开后的 6 个子开关一并写进 `project.yaml`，却在文件头注释里千叮咛万嘱咐“绝对不许写”？

## 答案提示

1. 不会。`one-shot-5-grow.md` 明确写死：Grow 只支持长成 Web（Vite + TypeScript）工程；如果你已经设定了非 Web 引擎，它会直白告诉你“往该引擎迁移的功能尚未实现”，让你自己用 `/setup-engine` 起步，原型只当可玩验证。
2. `rigor` 会撞上“Steam / 商业”与“周末 / 小项目”的冲突，通常会按卡片显式亮出推断理由由你通过 `Change something` 拍板；而 `project.goal` 规则写得很死——商业类压过兴趣/练手类，且 `early_access` 压过 `sell`，所以会推成 `early_access`。
3. 因为配置解析链里“显式写进 `project.yaml` 的值永远压过 `rigor` 展开”。一旦把 6 个子开关写死进文件，以后你通过 `/project-settings modes.rigor=full` 升档时，那 6 个键全都钉死了不会跟着变。
