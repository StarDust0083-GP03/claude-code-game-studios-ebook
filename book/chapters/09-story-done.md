# 第 09 章 验收：`/story-done` 如何堵死“基本完成”

## 场景：别听“应该没问题”，拿证据出来对账

程序员刚交差，总结写得漂漂亮亮：“已按要求实现全部验收标准。”换作平时，你扫两眼 diff 顺手就合并了，结果两天后一运行，菜单画到屏幕外面去了，或者某条边界逻辑压根没测过。

`/story-done` 是全仓库含金量最高的一个技能，它天生不信任何“口头汇报”。进门先翻账本，把故事的每一条验收标准摊在桌上，逐条拿证据拷问：这条有测试文件吗？这条有亲眼打开看过的截图吗？这条用户真测过吗？代码改完后截图有没有过期？AI 自己偷偷拍的那些数值和文案，你点头了吗？

只要有一条没着落，它就宁可停在 `NOT ASSESSED`，绝不让你糊里糊涂签字放行。

## 证据分级表：什么能省，什么死活不能省

`/story-done` Phase 1 拿 `qa.level`（注意：直接读 `qa.level`，不拿 `workflow` 或 `rigor` 替代，所以你可以“文档走 `minimal`，质检走 `standard`”）定出四档规矩：

| 检查项 | `qa.level: minimal` | `qa.level: standard` | `qa.level: full` |
|---|---|---|---|
| Logic / Integration 测试文件 | 豁免 | 必需 | 必需 |
| Config/Data 冒烟报告 | 豁免 | 必需（默认建议级） | 必需（默认阻断级） |
| Visual/Feel / UI 留存截图 | **必需** | **必需** | **必需** |
| 未测试的验收标准 | 从不升级阻断 | 超过一半则阻断 | **哪怕一条未测就阻断** |

盯住第三行：**截图在所有档位——包括最轻的 `minimal`——都不豁免**。因为单元测试全绿，依然拦不住按钮重叠、文字出框或材质丢失。另外 Visual/Feel 故事除了截图，还多要一份 `production/qa/evidence/<story-slug>-evidence.md` 的签字表（单人开发可以自己把所有角色都勾成 `[x] Approved`）；UI 故事只要留存截图，不用额外填签字表。

## 三种核对方式：划清“模型能验什么”和“只能人来验什么”

Phase 3 规定每条验收标准只能走三条路之一，严禁混着糊弄：

1. **看（Checked by looking）**：查文件在不在、测试文件在不在、玩法代码里有没有硬编码魔法数字、有没有漏进本地化的界面字符串（先解析代码根；解析不出必须报 `NOT ASSESSED — code root unresolved`，绝不报“零违规”）。这里有条死规矩：**报告里只准写 `test file present`，永远不准写 `test passes`**，因为 `/story-done` 根本没替你跑测试。
2. **问（Asked）**：涉及真实行为（“玩家挨打时扣血并闪白”）、手感、性能的标准，**严禁模型看了两眼代码就替你判通过**——代码只说明“作者想让它干嘛”，不说明“跑起来真干了嘛”。一次最多问 4 条，v1.3.0 给了四个非常顺手的选项：
   - `Yes — passes`（通过）
   - `No — fails`（失败 → 直接 `BLOCKED`）
   - **`I'll check it when I play`**（v1.3.0 新增！标成 `DEFERRED — requires playtest session`，先记下等试玩再看，不再把验收卡死）
   - `Not tested yet`（标成 `UNTESTED`，只要有一条，判决最高就只能停在 `NOT ASSESSED`）
3. **看屏幕（Seen on screen）**：凡是屏幕可见结果，必须真的打开 `production/qa/evidence/<story-slug>/` 下的截图肉眼核对。**严禁描述没打开看过的图片，也严禁把上一棒检查点里的 `Run result: OBSERVED` 文字当成自己亲眼看过**（引用可以，必须标明这是 `/dev-story` 的转述）。v1.3.0 顺手给 Grow 出来的 Web 工程开了个合理绿灯：只要打开看过同种子回放生成的 `story.png` 且画面清清楚楚展示了某条标准，直接算“看屏幕”覆盖，不用再弹窗追问用户一遍。

核对完拼出一张可追溯表（验收标准 | 证据路径或结论 | `COVERED` / `UNTESTED`），哪条做实了、哪条悬着，一眼扫穿。

## 内容哈希回执：专治“截完图又偷改代码”

研发里有个特别阴的坑：上午截了一张漂亮的图存进证据目录，下午随手改了两行战斗数值，忘了重截。验收时图还在、代码也改了，结果拿过期的旧截图盖了新代码的章。

CCGS 用 `.claude/scripts/review-receipts.sh` 堵死这个漏洞。`/dev-story` 截完图时，顺手给改动过的代码文件算内容哈希，写进截图旁边的 `stamp.txt`：

```text
Reviewed-Content-Hash: src/combat/parry.gd a1b2c3d4...
```

到了 `/story-done` 跑 `review-receipts.sh check stamp.txt`，立刻原形毕露：
- 文件没动过：`UNCHANGED: <path>`
- 截完图又改过：`CHANGED: <path>` → 直接提示“这个文件在截图之后改过，去重拍！”
- 文件删了：`GONE: <path>`
- 老证据没留 `stamp.txt`：`RECEIPT: NONE` → 老实报“没有回执，没法判断截图是不是比代码旧”，绝不静默放行。

为什么费劲用**文件内容哈希**，而不用更省事的 `git diff` 或文件修改时间 `mtime`？源码注释里把账算得很明白：
- `git diff` 依赖已提交基线，未提交草稿阶段不好用；
- `mtime` 在云盘同步、切分支、备份恢复时经常撒谎——万一一次同步把修改时间抹回旧时间，新改坏的代码就会悄悄逃过复核（这是最致命的**假阴性**）；
- 内容哈希只认字节内容，最多因为改了个注释多提醒你一次（**假阳性**，浪费点时间但绝不漏检）。另外脚本还专门处理了 Windows 回车符 `\r`，避免在 Windows 上打的回执放到 Linux/macOS 上全员误报 `CHANGED`。

（注意：回执过期的提示属于信息行，会大声报出来提醒你，但不会强行把 `COMPLETE` 降级。）

## 范围检查 + v1.3.0 新增的 `Own calls` 追认

Phase 5 除了对照 GDD、ADR 和控制清单抓偏差（按 `BLOCKING` / `ADVISORY` / `OUT OF SCOPE` 三级标清），还有两件特别接地气的检查：

1. **改动范围核对**：拿故事里 `## Files` 清单去对 `git status --porcelain`。清单之外冒出来的改动标成 `OUT OF SCOPE`（v1.3.0 补了一个贴心逻辑：如果那个文件属于同一史诗下已经关闭、但还没提交的另一个故事的 `## Files`，就不误报越界）。要是工作区干干净净没任何未提交改动，就老老实实写 `Scope: not checked — no uncommitted changes to compare`，绝不把“没东西可比”当成“范围全对”。
2. **把 AI 擅自拍的板全拎出来（`Own calls`，v1.3.0 重头戏）**：写代码时不可避免要定一堆设计文档没写的细节——比如“金币每秒掉 70 像素”、“暴击字样用亮黄色”、“背包满了直接把新东西掉在地上”。以前这些全藏在代码里，玩家和策划根本不知道。v1.3.0 强制 `/story-done` 对照改动文件、简报/GDD 和 `/dev-story` 检查点里的 `Own calls`，把所有**玩家看得到、或者后续故事必须对齐的 AI 自主决定**一条条用大白话列出来，不管开没开自动模式，逐条问你：**“留着，还是改？”**
   - 你选 **Keep it**：关故事时记进故事末尾的 `## Calls beyond the design`，以后成了正式约定；
   - 你选 **Change it**：直接变成一条 **`BLOCKING` 阻塞项**，故事不准关，打回 `/dev-story` 按你的话改完再来验收；
   - 压根没文件可读：直接算一条 `NOT ASSESSED`。

另外，如果这是从原型 Grow 出来的 Web 工程，Phase 4 还会盯住 `Same-seed run:`：只要上次 `/dev-story` 的同种子回放是 `CHANGED, not accepted`，在任何模式下都是**硬 `BLOCKING`**；如果压根没跑过同种子回放，直接停在 `NOT ASSESSED`。

## 四态判决：为什么“不知道”必须压在“通过”头顶

过完 Phase 6 的评审门（注意 `Reviewed by` 永远不准留空——真跑了填 `lead-programmer`，`lean` 模式下你说自己跑过 `/code-review` 会老实写上 `/code-review (you said you ran it; not verified here)`，`solo` 或没跑就直白写 `self, no independent review`），就到了最终裁决。

![四态判决的优先级：失败高于未知，未知高于通过](../../wiki/assets/diagrams/verdict-order.svg)

判决顺序写得死死的，从上往下撞上哪条算哪条：

1. **`BLOCKED`（失败）**：有验收标准挂了、存在 `BLOCKING` 缺口/偏差、有被你打回要改的 `Own call`，或者 Grow 游戏的同种子回放变了且你没点头。
2. **`NOT ASSESSED`（无法评估）**：有标准没说清可观察结果、你答了“还没测”、评审门缺输入、证据读不了、对账用的 GDD/ADR 丢了，或者读不到改动文件导致 `Own calls` 没法审。
3. **`COMPLETE WITH NOTES`（带备注通过）**：所有标准都通过或合理延期（`DEFERRED`），但还挂着建议级（`ADVISORY`）事项。
4. **`COMPLETE`（全通过）**：全部通过，零建议项。

这两条排队规矩，专治 AI 验收时的两种歪风：
- **绝不拿“没测过”混成“通过”**：只要还有一项不知道行不行，就算其他十项全绿，最高也只能停在 `NOT ASSESSED`；当然，真测出 bug 挂了肯定最严重，排第一。
- **绝不拿无关痛痒的流水账扣分**：像截图回执信息、没有冲刺计划文件、运行结果说明这些纯信息行，记一笔就行，绝不因此把一份干干净净的 `COMPLETE` 硬降级成 `COMPLETE WITH NOTES`，免得警告泛滥以后大家全麻木了。

## 关闭与精准提交：绝不偷跑 `git add -A`

判决出来后，`/story-done` 绝不自己直接改状态，而是亮出选项让你拍板（哪怕开了 `autonomous`，强行关闭一个带偏差或未通过的故事也属于 `scope_changes`，照样停下来问你）。

只有你明确点头关闭，它才依次动手：
1. 把故事 `Status` 改 `Complete`，追加 `## Completion Notes` 和 `## Calls beyond the design`；
2. 如果你选了记技术债，往 `docs/tech-debt-register.md` 加行；
3. 同步更新 `production/sprint-status.yaml`、`EPIC.md` 里的对应行，以及 `minimal` 档下 `design/game-brief.md` 对应的 `[x]` Feature 勾选框；
4. **v1.3.0 新增：主动问你一句 `Commit this story? (feat: [story title])`**。如果你选 `Yes, commit`，它**只用 `git add -- <本故事 ## Files 和本次改到的文档>` 精准暂存再提交，明令禁止 `git add -A` 或 `git add .`**，绝不顺手把你工作区里做到一半的其他改动一起打包进历史。

如果你选了“先别关”，它一个文件都不动，也**绝不自作主张去帮你修挂掉的验收标准**，只把要改什么清单交给你，等你决定下一步。

## 常见误解

- **误解一：`minimal` 档验收走个过场，什么证据都不要。** 错。单测可以豁免，但凡玩家看得见的画面，截图照样是硬门槛；Grow 出来的工程还得验同种子回放。
- **误解二：`/story-done` 发现测试通过了，说明代码肯定没 bug。** 它从来不声称“测试通过了”，只查测试文件在不在，真跑测试靠你自己（或 Web 的 `npm run smoke` / `npm test`）。
- **误解三：验收不过，AI 会顺手把问题改好再关。** 源码里明确禁止 `/story-done` 自己动手修挂掉的标准——验收官不能既当裁判又偷偷改卷子，要改必须退回 `/dev-story`。

## 练习

1. 如果你在 `/story-done` 的行为确认问题里，选了 `I'll check it when I play` 和选了 `Not tested yet`，最终判决会有什么本质区别？
2. 为什么 `review-receipts.sh` 宁可承受“改了行注释也报 `CHANGED`”的假阳性，也坚决不用 `mtime`？
3. 假设你刚做完一个“商店界面”故事，程序员擅自把刷新商店的价格定成了 `50 金币`（简报里没提价格），在 v1.3.0 的 `/story-done` 里，这个决定会经过哪几个步骤？

## 答案提示

1. 选 `I'll check it when I play` 会标成 `DEFERRED — requires playtest session`，它不阻断也不拉低成未知，配合其余全绿时可以走到 `COMPLETE WITH NOTES`；而选 `Not tested yet` 会标成 `UNTESTED`，最高只能停在 `NOT ASSESSED`（在 `full` 档下甚至直接阻断变 `BLOCKED`）。
2. 因为 `mtime` 在备份恢复或云同步时可能倒退，导致已经改坏的代码披着旧时间戳逃过审查（假阴性漏检），风险远高于多看一眼截图的成本（假阳性）。
3. `/dev-story` 会要求程序员在总结和检查点的 `Own calls` 里报出“刷新商店定价 50 金币”及其文件位置；到了 `/story-done` Phase 5，它会单独拎出来问你“Keep it 还是 Change it”。选 Keep 就写入故事的 `## Calls beyond the design` 成为正式设计；选 Change（比如改成 20 金币）就直接标成 `BLOCKING`，故事不准关，打回 `/dev-story` 修改。
