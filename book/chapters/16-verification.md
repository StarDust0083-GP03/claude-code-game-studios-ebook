# 第 16 章 验证与演进：Markdown 写的框架，怎么证明自己没改坏

## 场景：你魔改了两个技能，怎么知道没把流程拆散架

CCGS 本身就是个鼓励你按自己团队习惯魔改的模板。今天你改了 `/dev-story` 的 Phase 5，明天删掉了两个用不上的角色。普通代码改完有编译器和单元测试兜底，可技能和角色全是 Markdown 文本，没有编译器报错——改坏了往往要等跑崩一次真实任务才发现。

CCGS 给出的解法，是把一套专门测“框架自己”的质检设施随模板一起打包在根目录的 **`studio-tests/`** 里，用 `/skill-test` 和 `/skill-improve` 两个技能驱动。

## `studio-tests/` 里面到底装了什么

先说清一个极容易混淆的目录分工：**`tests/` 是留给你放游戏测试的（刚克隆的模板里没有框架自测代码）；`studio-tests/` 才是用来测 CCGS 自己的技能和角色的。**

打开 v1.3.0 仓库里的 `studio-tests/`，结构非常完整：
- **`catalog.yaml`**：主花名册，登记了全部 **75 个正式技能**（v1.3.0 同步把旧名规格改成了 `next-step.md`、`project-settings.md`、`write-changelog.md`，并新增了 `cut.md`）和 **49 个角色**，追踪各自的优先级、分类以及上次测试时间与结果。
- **`quality-rubric.md`**：按技能类别（`gate`、`review`、`authoring`、`readiness`、`pipeline`、`analysis`、`team`、`sprint`、`utility`）定好的通过门槛。
- **`skills/` 与 `agents/`**：每个技能、每个角色各有一份行为规格文件（spec），比如 `gate-check.md` 里写死了要检查它读没读评审模式、solo 模式下是不是跳过全部门禁、是不是禁止自动推进阶段。
- **`templates/`**：给你自己新写的技能/角色抄的规格模板。
- **`results/`**：跑完测试后存放报告的目录（注意它没进 `.gitignore`，不想提交结果的话要自己加进去）。

文档甚至诚实地列了一张“如果嫌占地方把 `studio-tests/` 删了会怎样”的账单：
- `/skill-test static`：照常能跑（只读技能文件本身）；
- `/skill-test audit`：降级（报找不到花名册）；
- `/skill-test spec` 和 `category`：直接罢工；
- `/skill-improve`：失去按类别的打分循环。

## 四种检查模式与 `skill-lint.sh` 静态体检

驱动这套质检的 `/skill-test` 分四个模式：`static`（7 项结构检查）、`spec`（逐条对照行为规格）、`category`（对照类别打分表）、`audit`（出覆盖率全景报告）。其中唯一纯靠脚本确定性运行的，是 `static` 背后的 `.claude/scripts/skill-lint.sh`。

拿它扫单个技能（比如 `bash .claude/scripts/skill-lint.sh dev-story`），它会把技能的主 `SKILL.md` 连同 `references/` 下的拆页一起读完，吐出 7 项冷冰冰的客观数据：
1. `check1`：YAML 前置元数据齐不齐、`name` 和目录名对不对得上；
2. `check2`：阶段数和二级标题数；
3. `check3`：出现了哪些判决词（如 `BLOCKED`、`COMPLETE`、`FAIL`）；
4. `check4`：有没有写“写入前请示批准”以及声明的写工具；
5. `check5`：最后一节标题是什么、点名了哪些下一步技能；
6. `check6`：有没有用独立上下文（`context: fork`）；
7. `check7`：参数提示（`argument-hint`）和参数解析段落。

全仓扫描 `bash .claude/scripts/skill-lint.sh all` 时，脚本最后一行一定会报实测读到的总数（在 v1.3.0 上，因为目录里有 75 个正式技能 + 3 个旧名转发层 `help`/`settings`/`changelog`，磁盘上一共 78 个 `SKILL.md`）。如果某个文件读失败，脚本专门打印 `NOT_READ` 且不计入已读计数，绝不拿“扫了 70 个没报错”冒充全仓通过。同时它依然只报观察数据，具体“这样算不算合格”留给 `/skill-test` 去判。

## 写门禁与技能的五条铁律（`.claude/rules/skill-authoring.md`）

全仓库最值得打印出来贴墙上的规范，其实是 `.claude/rules/skill-authoring.md` 里的五条铁律——哪怕你不做游戏，只要给公司写 AI Workflow 或 CI 门禁，条条都扎心：

1. **任何门禁必须有“无法评估（`NOT ASSESSED`）”这一档，而且必须排在通过之上、失败之下。** 只有“通过/失败”二态的系统，最终一定会把所有拿不到数据、脚本没跑起来的情况偷偷塞进“通过”。
2. **缺了配置或路径时，绝不准默认成最宽松的值。** 写默认值前先问一句：“这个键框架里到底有没有人写？”如果压根没人写，你随手写的默认分支就是所有真实项目的线上行为（比如代码根解析不出绝不默认 `src/`）。
3. **跳过的检查必须在大屏输出里明说，不能只写在源码注释里。** 注释只有作者看，用户看到空输出只会以为检查跑过且全绿。
4. **没法溯源的事实不准断言，且发现的缺口必须接进最终判决里。** 光在正文里提醒一句“缺少某项证据”却不影响最终 Verdict，那条提醒就只是一行没人看的装饰废话。
5. **覆盖范围靠动态派生，绝不手写死白名单。** 手写死名单只要以后新增一个技能就会立刻漏检（像 `/project-settings` 动态 grep `effects-map.md` 的 `> ### RESERVED` 标题，就是这条铁律的活教材）。

旁边还附了两条特别毒辣的实操守则：
- **别写“碰巧就能为真”的断言**：比如检查字符串里有没有 `unity`，结果连 `community` 这个词都能命中导致假通过。
- **没亲眼见过它报错的门禁，根本不算门禁**：写完一个检查后，必须动手搞一次**变异测试**——故意把被守护的东西改坏，亲眼看着门禁红灯报警，再改回来变绿。

## 升级策略：别拿 `--allow-unrelated-histories` 给自己找几百个冲突

随着上游从 v1.2.0 演进到 v1.3.0，`UPGRADING.md` 总结出了一套非常务实的升级分流：

- **同源 clone 的项目（有共同 Git 历史）**：直接加 `template` 远程，`git fetch --tags template main && git merge template/main`，只解决你改过的 `CLAUDE.md`、`project.yaml` 等少数冲突即可。
- **ZIP 下载或独立 `git init` 的项目（无共同历史）**：**千万别硬敲 `git merge --allow-unrelated-histories`**，没有共同祖先会让 Git 把几百个模板文件全标成冲突。正确姿势是选策略 A2——用 `git checkout template/main -- .claude UPGRADING.md CHANGELOG.md studio-tests docs/engine-reference/web ...` 只精准拉框架目录到暂存区，看清 `git diff --cached --stat`，把你自己魔改过的文件逐个 `git checkout HEAD -- <file>` 救回来，`CLAUDE.md` 和 `project.yaml` 手工 `git diff` 合并。
- **升级顺序别搞反**：像 v1.2.0 → v1.3.0 这种更新，必须**先把 `.claude/hooks/` 和 `.claude/scripts/` 覆盖到位，再去合 `.claude/settings.json`**，不然新 `settings.json` 指向的新脚本还没落盘，每次调用都会报错。

## 诚实说清楚：这套验证到底覆盖不到什么

必须点破两个真实边界：
1. **`/skill-test` 全部四个模式都只读文件，从来不真的执行技能。** 连 `spec` 和 `category` 也是让大模型读完 `SKILL.md` 和规格文档后做“纸面代码审查”。它能保证结构规范没写漏、规矩没改丢，但**不能证明模型在真实多轮对话里 100% 乖乖照做**。
2. **模板仓里没有随附框架自己的单元测试套件。** `studio-tests/` 放的是针对技能/角色的静态与规格检查；而类似测试 `yaml-helper.sh` 几十个 YAML 边界、验证 `validate-commit.sh` 各种 shell 嵌套的自动化单测脚本，并没有打包进公开分发模板里（这也是为什么本书下一章专门用独立 Python 写了 17 个单测来亲手验证核心约束）。

## 常见误解

- **误解一：`/skill-test static all` 全过，说明我魔改的技能跑起来绝对没问题。** 错，它只验静态结构，不跑真实会话。
- **误解二：根目录的 `studio-tests/` 是用来测我写的游戏代码的。** 不是。游戏测试放 `tests/`（或 `Assets/Tests/` 等引擎测试根），`studio-tests/` 只测 CCGS 自己的技能和角色。
- **误解三：把 `studio-tests/` 删干净能让仓库更清爽且没副作用。** 会直接弄废 `/skill-test spec` 和 `category` 两个模式。

## 练习

1. 如果你给自己的项目改写了一个技能，按 `skill-authoring.md` 的五条铁律，设计一次最小“变异测试”来确认你加的检查门禁真的有效。
2. 为什么 `/skill-test spec` 即使通过，也不能完全替代用真实游戏跑一遍 `/dev-story`？
3. 假设你是从 ZIP 下载的 CCGS v1.2.0 启动了项目，现在想升到 v1.3.0，为什么 `UPGRADING.md` 严禁直接把 `project.yaml` 和 `CLAUDE.md` 也放进 `git checkout template/main -- ...` 命令里？

## 答案提示

1. 比如在技能里加了“禁止硬编码密钥”或“坏 JSON 必须阻断”的检查后，先故意构造一份坏 JSON 或假密钥提交/写入，确认脚本或门禁确实触发 `exit 2` 或打出 `BLOCKED`；恢复正常后再跑一遍确认放行。
2. `spec` 是大模型读文本做静态对照，只能验证“步骤和规则写进去了”，验证不了真实执行时的工具权限弹窗、脚本跨平台兼容、上下文压缩后的遗忘率，以及模型在复杂代码里的实际遵循度。
3. 因为 `git checkout template/main -- <file>` 会整文件覆盖，直接把你自己配好的 `engine.name`、`modes.rigor`、`project.goal` 和 `CLAUDE.md` 里的技术栈/引擎引用一行不剩全洗白；这两个文件必须保留本地版，只看 `git diff` 手工合入新结构。
