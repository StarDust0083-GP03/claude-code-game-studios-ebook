# 第 09 章 验收：`/story-done` 如何区分事实与断言

## 场景

故事报告说"实现完成，所有验收条件满足"。`/story-done` 不采信这句话。它把每条验收标准摊开，逐条问：这条有测试文件吗？这条有截图吗？这条你亲眼看过了吗？这条需要试玩吗？

答案分成几种：有人看到过、有文件存在、用户口头确认、没人验证。四种状态对应不同判决。

这一章讲验收协议。它比实施流程更值得借鉴，因为大多数团队的"完成"定义比这里模糊。

## 证据分级

`/story-done` 的 Phase 1 有一张按 `qa.level` 分列的表：

| 检查 | minimal | standard | full |
|---|---|---|---|
| Logic、Integration 测试 | 豁免 | 必需 | 必需 |
| Config/Data 冒烟报告 | 豁免 | 必需，默认建议 | 必需，默认阻断 |
| Visual/Feel、UI 截图 | 必需 | 必需 | 必需 |
| 未测试的验收条件 | 从不升级 | 超过一半阻断 | 任何一条阻断 |

注意第三行：截图在所有档位都必需，包括 minimal。理由在 README 里："解析检查不是运行"。一个菜单画到屏幕外，测试仍然全绿。

第四行是档位差异最明显的地方。minimal 允许未测试条件存在但不升级；standard 在一半以上未测试时阻断；full 遇到任何一条未测试就阻断。

## 三种核对方式

Phase 3 规定每条验收标准只能用三种方式之一核对。

第一，看。文件存在、测试文件存在、代码里没有本应在数据文件里的数值、玩家可见字符串没有硬编码。看只能证明"存在"，不能证明"正确"。所以报告里写"test file present"，永远不写"test passes"。

第二，问。行为、手感、性能这类条件必须问用户。一次最多四个问题，选项是"是，通过"、"否，失败"、"还没测"。"还没测"等于 UNTESTED，判决最高只能到 NOT ASSESSED。

第三，看屏幕。涉及可见结果的条件，需要 `production/qa/evidence/<story-slug>/` 下有一张**打开看过**的截图。技能明确禁止描述没打开过的图片，也禁止把检查点里 `Run result: OBSERVED` 的文字当成自己看过。

这三种方式划出了一条清晰的界线：模型可以检查产物，不能替用户确认体验。

## 可追溯表

核对完，生成一张表：

```
| 验收条件 | 由什么覆盖 | 状态 |
| AC-1: ... | tests/unit/combat/parry_test.gd::test_parry_window | COVERED |
| AC-2: ... | production/qa/evidence/story-003/01-sparks.png | COVERED |
| AC-3: ... | — | UNTESTED |
```

这张表是整个验收协议的产物。它让"哪条没做"变得具体，而不是一句"基本完成"。

## 证据会过期

有一段设计很细致：截图可能比代码旧。你先截了图，后来又改了数值，截图没重拍，验收时看起来通过。

`review-receipts.sh` 解决这个问题。`/dev-story` 截完图后，对改动的每个文件打内容哈希，写进 `stamp.txt`：

```
Reviewed-Content-Hash: <path> <hash>
```

`/story-done` 用 `check` 比对：

```
RECEIPT: <stamp.txt>
UNCHANGED: <path>
```

如果代码变了：

```
CHANGED: <path>
```

文件被删了则报 `GONE:`，收到从未展开的通配符报 `UNRESOLVED:`。没有回执时报 `RECEIPT: NONE`，并说明"无法判断证据是否比代码旧"。

在固定快照上实测一遍：

```bash
bash .claude/scripts/review-receipts.sh hash combat.gd > stamp.txt
bash .claude/scripts/review-receipts.sh check stamp.txt
# RECEIPT: stamp.txt
# UNCHANGED: combat.gd

echo "b" >> combat.gd
bash .claude/scripts/review-receipts.sh check stamp.txt
# RECEIPT: stamp.txt
# CHANGED: combat.gd
```

脚本头部解释了为什么用内容哈希而不是 git 或 mtime。`git diff` 需要一个已提交的基线；`git status` 只看未提交改动；mtime 在备份恢复和云同步下会说谎，一次旧 mtime 的恢复会让新内容悄悄逃过评审，这是危险的假阴性。哈希没有这些问题。剩下的失败方向是假阳性：重评审没变的东西，浪费 token，但不会漏评审。

还有一个刻意的例外：未被回执记录过的字面路径缺失时保持沉默。因为某些调用方每次都会传一个可选输入，报出来会打断合法的跳过。但回执记录过、现在消失的路径会报 `GONE`，因为上次评审确实读过它。

## 范围检查

Phase 5 对照故事的 `## Files` 和 `git status --porcelain`。改动文件不在清单里就标 OUT OF SCOPE，只作提示，不阻断。没有 `## Files` 段时，回退到会话检查点里的"进行中的文件"；两者都没有，报告 `Scope: NOT ASSESSED`。

工作区干净时报告 `Scope: not checked — no uncommitted changes to compare`。这句话避免把"没有改动"误读成"范围正确"。

## 四态判决

Phase 7 规定的判决顺序是固定的，第一条匹配就生效：

1. BLOCKED：某条验收条件失败，或存在阻断级的缺口或偏差。
2. NOT ASSESSED：某条条件无法评估。比如它没说清可观察结果、用户答"还没测"、评审门返回 NOT ASSESSED 且输入没补上、证据存在但读不了、缺少判定偏差所依据的 GDD 或 ADR。
3. COMPLETE WITH NOTES：所有条件通过或延期，但存在建议级事项。
4. COMPLETE：全部通过，没有建议级事项。

顺序里有两条设计意图。

第一，NOT ASSESSED 排在两个通过态之上。无法评估的一部分，不能当作整体良好。这对应 `skill-authoring.md` 的第一条义务：每个判决都要有"无法评估"这个值，并且它要排在通过之上、失败之下。

第二，信息行不算建议项。证据时间戳、缺少冲刺文件、运行结果这些只是信息，不会把 COMPLETE 变成 COMPLETE WITH NOTES。这个区分防止一份干净的故事因为环境差异被降级。

## 关闭是一次显式决定

判决出来之后，技能会问："你想怎么处理？"

选项是：关闭并记录、关闭并把建议项记为技术债、先别关我要修、或者接受偏差直接关。

只有在用户明确选择关闭时才写文件。BLOCKED 或 NOT ASSESSED 时，推荐选项是"先别关"，并列出要改什么。技能还规定：不许自己修复失败的条件，只报告并询问。

如果 `automation_always_ask` 列表包含 `scope_changes`，那么即使当前是 autonomous 模式，关闭一个带偏差的故事仍然会提问。因为关闭动作改变了范围承诺。

## 常见的验收漏洞

第一个漏洞：把测试文件存在当成测试通过。整套流程只检查存在性，运行测试是用户的责任。技能在实施结束时明确提示："先跑你的测试套件并确认新测试通过，再关闭故事。"

第二个漏洞：把模型描述当成观察。截图必须被打开看过，`OBSERVED` 文字只是上一阶段的描述，引用时要标明来源。

第三个漏洞：证据比代码旧。哈希回执解决这个，但前提是实施阶段真的写了 `stamp.txt`。没有回执时，脚本诚实地说"无法判断"，而不是默认通过。

## 常见误解

误解一：minimal 档什么证据都不用。截图仍然必需，只是自动化测试豁免。

误解二：判决由模型自由裁量。四态有严格优先级，还有一张按档位的阻断表。

误解三：关闭故事会自动提交代码。技能只打印一条建议的 `git add` 和 `git commit` 命令，不执行。

## 练习

1. 在临时目录里创建文件、打哈希回执、修改文件，观察 `check` 的输出变化；再删掉文件，看 `GONE`。
2. 一条验收条件写"格挡手感要扎实"，按验收协议它应该怎么被处理？判决会是什么？
3. 解释为什么 NOT ASSESSED 排在 COMPLETE 之上、BLOCKED 之下。

## 答案提示

1. 依次得到 UNCHANGED、CHANGED、GONE。没有回执时得到 `RECEIPT: NONE` 和每个文件的 NEW。
2. "手感"无法靠看文件确认，也不能靠单张截图证明，属于需要试玩的条件，标记 DEFERRED 并要求试玩记录。若没有任何可观察定义，判决停在 NOT ASSESSED。
3. 无法评估意味着没有建立"良好"的证据，所以不能算通过；但已知的失败更可操作，所以排在 BLOCKED 之后。这个排序避免了把访问问题伪装成通过，也避免把真实失败埋在未知后面。
