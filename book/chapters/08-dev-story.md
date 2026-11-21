# 第 08 章 实施链路：`/dev-story` 怎么把故事变成代码

## 场景：别信模型写的漂亮总结，先看硬盘上有没有文件

你手里已经有一份就绪的故事 `production/epics/stealth/story-003-melee-parry.md`：Core 层、Logic 类型、ADR 已批准、前置依赖都已关闭。敲下 `/dev-story production/epics/stealth/story-003-melee-parry.md`。

接下来发生的事，拆开看其实是两条并行推进的线：**一条管“往模型脑子里喂什么上下文”，另一条管“硬盘上到底落了什么文件、跑出了什么结果”**。v1.3.0 还在这条链路上补齐了 Web 引擎的冒烟检查、Grow 项目的同种子回放，以及让程序员老实招供自己擅自拍了哪些板（`Own calls`）。

## 第一步：先用脚本把故事读成事实表

技能不会一上来就靠记忆猜故事在哪，而是先调 `.claude/scripts/story-facts.sh <story-path>` 抓出一张 TSV 事实表：状态、类型、架构层、TR-ID、ADR、验收标准条数、测试证据状态、前置依赖。要是你敲 `/dev-story` 没带参数，它先看 `active.md` 检查点里的当前任务向你确认；检查点里也没有，就跑 `story-facts.sh --all` 把所有 `TODO` 故事列成选项让你选。

记住仓库那条铁律：脚本只吐观察结果，绝不下结论。盘里一个故事都没有时，直接停止并告诉你先去跑 `/create-stories`，不乱猜。

## 第二步：按系统算档位，不拿全局 `rigor` 一刀切

正文开头 `!` 注入的配置里已经带齐了 `workflow`、`qa.level`、`gate_level`、`specialists`、`perf_budgets`、`system_overrides`。注意 `/dev-story` 决定前置检查有多严时，看的是**当前故事所属系统的 `workflow` 档位**：从故事的 `GDD:` 路径提取系统名，先查 `system_overrides` 里有没有单独给这个系统加码，没有再退回全局 `workflow`。

所以你可以整仓跑 `minimal` 快速推进，唯独把战斗系统钉在 `full`——写到战斗故事时，Phase 2 自动严查注册表和 Accepted ADR，写别的系统照样轻装上阵。第一条回复就会明确印出 `Tier: workflow <value>`，绝不把 `rigor` 或 `qa.level` 混进来用。

## 第三步：前置门禁（不通过直接写 BLOCKED，不派代理）

Phase 2 照着三列表拦门：

| 前置输入 | `full` | `standard` | `minimal` |
|---|---|---|---|
| TR 需求注册表 | 缺失直接停（让你先 `/architecture-review`） | 可选 | 不要求 |
| 故事点名的 ADR | 缺失 / `Proposed` / `Deprecated` / `Superseded` 直接停 | 故事点名了才查 | 故事点名了才查 |
| 控制清单 | 缺失发警告，继续 | 缺失发警告，继续 | 不要求 |

这里有两处很实的防呆：
- **ADR 默认不打开原文**：先调 `adr-status.sh <ADR-ID>` 拿状态和版本号，跟故事里的 `ADR Version` 对得上就直接信故事摘要；对不上才去读 `references/version-mismatch.md`。
- **依赖故事逐个核查**：对每个前置依赖跑 `story-facts.sh`，只要不是 `COMPLETE`，立刻停下来问你三个选项——自担风险硬上、先停下做依赖、还是其实做完了只是忘了改状态（选第三个也会先问你“能把依赖故事改成 Complete 吗”再动手）。

只要上面任何一项触发了停止，**绝不派程序员代理**，直接跳去 Phase 7 写一条 `BLOCKED` 检查点收尾。通过了则进 Phase 3，只问一次能不能把故事标成 `In Progress`（如果你拒绝，它不改状态文件，但照样往下写代码，并在总结里诚实记一笔 `Story not marked In Progress — declined`）。

## 第四步：代码根不瞎猜

写代码前必须先算清代码往哪放。按 `.claude/docs/code-root-resolution.md`（详见第 13 章），先查 `project.yaml` 的 `engine.code_root`（填错了直接报 `invalid` 不回退），再查 `engine.name` 对应 `.claude/engines/engines.tsv` 的行，再查旧版 `technical-preferences.md`，最后才在 `src/`、`Assets/`、`Source/` 恰好只存在一个时做无歧义推断。

**要是怎么都解析不出来，或者配置非法，直接罢工不写**。绝不偷懒默认往 `src/` 塞——因为在 Unity 里往 `src/` 写代码根本不参与编译，写几百行全白干；测试放错目录更坑，Unity 测试运行器直接给你绿油油地印出一行 `0 tests, Passed`。

## 第五步：按表派人 + 蒸馏简报

Phase 4 的选人规则很简单：Config/Data 类型的故事根本不用派代理，直接在主会话里列出 `旧值 → 新值`，征得你同意就改数据文件跳去 Phase 6；代码故事按架构层和类型派给对应的通用程序员（Foundation → `engine-programmer`，UI → `ui-programmer`，Visual/Feel → `gameplay-programmer`，AI → `ai-programmer`，网络 → `network-programmer`）。

写完后再把改动文件交给引擎专家过一遍引擎 API 坑点（只审查、吐出“文件 + 行号 + 问题 + 修法”，不直接改代码；破验收标准的打回给程序员修一次）。槽位直接读配置里的 `specialists`（靠 `code` 槽位区分 Godot GDScript 和 Godot C#）。注意 v1.3.0 对 **Web 引擎** 的处理：Web 没有单独的引擎专家角色，直接由 `lead-programmer` 对照 `docs/engine-reference/web/` 顶上。

Phase 5 写给程序员的简报特别讲究，绝不把几十 KB 的文档整篇粘贴进去，而是精准投喂：
- 给路径：故事文件、TR 注册表精确匹配行、控制清单对应层章节、命名规范、性能预算、测试路径；
- 给内联：故事里的 ADR 摘要和实施说明（**故意不给 ADR 原文路径**）；
- 缺什么就明说：Phase 2 没用到的输入（比如 `minimal` 下没有注册表），明确告诉子代理“这档位本来就没有，别浪费回合满仓库瞎找”，顺手也通知你一句；
- 按 `qa.level` 定测试要求：`minimal` 时必须白纸黑字写一句“**不要写测试文件**”（省略不说，模型以为你忘了，会顺手照着通用角色规范把单测写了）；`standard` / `full` 要求每条验收标准至少配一个确定性测试（禁随机种子、禁时间敏感断言、禁外部 I/O）；
- **v1.3.0 新增的两条代码规矩**：新增玩法数值必须写进数据文件（Grow 出来的 Web 项目放 `data/config.json` 并在 `data/config-notes.md` 记一行），不准硬编码；同时禁止写只用一次的过度抽象、禁止给不可能发生的分支加防御、禁止为了过测试硬写特判；最后要求程序员在汇报里**老实交待 `Own calls`——凡是设计和故事没写死、由它自己拍板定的数值、时机、颜色、边界行为和界面文案，逐条报出位置**，等着 `/story-done` 交给人类裁决。

## 第六步：先验硬盘产物，再做解析、看图和同种子回放

Phase 6 是整条实施链路里最硬核的一段，一共卡了五道关：

1. **先看有没有半途而废**：子代理撞上 `maxTurns` 或者半截停掉，必须大字报 `INCOMPLETE`，列出已有进展和断点，绝不准顶着“Implementation Complete”蒙混过关。
2. **触发器 0——先看硬盘文件，再信汇报**：不管子代理总结写得多天花乱坠，它点名改过的文件要是硬盘上压根不存在，直接判这一步失败，拉起子代理指着缺失文件返工。
3. **检查测试文件在不在**：`standard` / `full` 下查 Logic/Integration 故事的测试文件有没有落盘（依然只查存在性，绝不替你吹牛说“测试全过了”）。
4. **引擎级解析与冒烟检查**：
   - **Godot**：必须先跑 `godot --headless --path . --import`，再跑 `godot --headless --path . -s res://.claude/scripts/godot-parse-check.gd -- res://<改动的 .gd>`（看 `PARSE FAIL:`）。明令禁止拿 `--check-only` 敷衍，也禁止只跑 `--import` 就敢说解析过了。
   - **Web（v1.3.0 新增）**：只要 `package.json` 里有 `smoke` 脚本，每个故事做完必跑 `npm run smoke`（包含 `tsc --noEmit` 类型检查、单文件构建和 Playwright `@boot` 启动测试）。明确点破：光跑 `npm run build:single` 只证明编译过，不证明网页能打开；绝不跑 `commands.run`（那是永不退出的 dev server）。
   - **没装引擎或没跑 `npm ci`**：老老实实报 `parse NOT VERIFIED — <原因>`，严禁读两眼代码就嘴硬“看着应该能编译”。
5. **运行观察（Run and Observe）+ 同种子回放（v1.3.0 新增）**：
   - 凡是玩家看得见的东西（不只限 UI 和 Visual/Feel，哪怕 Logic 故事改了画面也算），**哪怕在 `qa.level: minimal` 也不豁免**：直接进改动场景截屏存到 `production/qa/evidence/<story-slug>/`，用 `review-receipts.sh hash` 把改动文件的内容哈希打进 `stamp.txt`，再亲自打开图片对照验收标准看一遍。最后只能输出一行纯文本 `Run result:`（`OBSERVED` / `NOT VERIFIED` / `N/A`，且 `N/A` 必须说清为什么真的不可见，拿“这是个 Logic 故事”糊弄会被 `/story-done` 直接拒收）。
   - **如果是从 `/prototype` Grow 出来的 Web 工程**（检测 `production/qa/evidence/grow-<name>/replay.args` 存在），每个故事做完不管什么类型，都要再跑一遍 `npm run build:single` + `bash .claude/scripts/one-shot-grow.sh replay <name> --as story`，拿同一颗随机种子和同一串按键把游戏重跑一遍，把新截图 `story.png` 和基准图摆在一起看：
     - `match yes` → `Same-seed run: SAME — nothing broke`；
     - **`match no`（或冒出新报错）**：不管开没开 `autonomous` 自动模式，**强制停下来把差异和两张截图甩给你看**——问你“这个故事改了同种子回放结果，是你想要的吗？”你点头才调 `one-shot-grow.sh accept <name>` 刷新基准；你说不是，故事直接打回 `INCOMPLETE` 等修复。

## 第七步：收尾账本

Phase 7 按固定模板出总结（包含改动文件、测试证据、验证命令和退出码、逐条验收标准、偏差、引擎风险、阻塞项、以及 v1.3.0 新增的 `Own calls`），用 `md-section.sh replace` 把实际改动文件覆写进故事的 `## Files`（绝不走 shell 重定向，免得绕过写入检查 Hook），再用 `session-state.sh checkpoint` 覆写 `active.md` 检查点（带上 `Run result:`、`Same-seed run:` 和 `Own calls:` 传给下一棒 `/story-done`），最后落上标准收尾块。

## 常见误解

- **误解一：`/dev-story` 跑完就等于故事验收通过了。** 不是。它只管把代码写出来、过解析/冒烟/截屏和同种子回放，并把真相打包进检查点；真正逐条核对验收标准和签字关闭是下一章 `/story-done` 的事。
- **误解二：测试文件存在就代表单元测试全绿。** 在 Godot / Unity / Unreal 路线下，`/dev-story` 明确提醒你：“去跑你的测试套件确认新测试通过，再敲 `/story-done`——它只查测试文件在不在，不替你跑。”
- **误解三：Grow 出来的项目改了一个新功能，同种子回放报 `match no` 就说明写炸了。** 不一定。新功能本来就可能改变游戏流程，所以框架不是直接判死刑，而是把“具体哪一行状态、哪一帧画面变了”亮到你面前，由你拍板这是“预期新行为（更新基准）”还是“改坏了老逻辑（打回返工）”。

## 练习

1. 在 `qa.level: minimal` 下，为什么 `/dev-story` 的程序员简报必须显式写一句“不要写测试文件”，而不能把测试那一节直接删掉？
2. 为什么在 Web 工程的 Phase 6 里，规则专门强调“光跑 `npm run build:single` 不算通过解析检查，必须跑 `npm run smoke`”？
3. 设想一个 Grow 出来的塔防游戏，你刚做完“新增冰冻塔”的故事，同种子回放（老按键脚本压根没造冰冻塔）却报了 `match no` 且显示第 12 秒怪物位置偏了。你应该选 accept 还是打回？这说明同种子回放抓住了什么问题？

## 答案提示

1. 因为 `.claude/agents/gameplay-programmer.md` 里写着“必须为所有玩法逻辑写单元测试”。如果简报里干脆不提测试，子代理就会照通用人设去写单测，导致行为跟 `minimal` 档位打架。
2. `build:single` 只证明 TypeScript 编译和打包没报错，看不出页面在真实浏览器里能不能启动、会不会一进页面就抛运行时异常白屏；`npm run smoke` 会把打包产物拉进 Playwright 跑 `@boot` 冒烟，才算验了启动。
3. 必须打回。老按键脚本根本没触发新功能，同种子回放结果本应 100% 一致；位置偏移说明你在写冰冻塔时意外动到了随机数消耗顺序（`rng()` 调用次序）或公共寻路/帧步进逻辑，这就是回归 bug，同种子回放正好把它抓了个现行。
