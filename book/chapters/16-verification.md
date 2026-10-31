# 第 16 章 验证与演进：这门框架怎么证明自己没坏

## 场景

你改了 `dev-story` 的一个阶段，加了两条规则。怎么知道没把技能改坏？

普通软件有编译器、单元测试、集成测试。技能是 Markdown，没有编译器。CCGS 的答案是一套针对技能本身的静态检查和行为规格。

## studio-tests

`studio-tests/` 是"测试技能和角色"的目录，不是测试游戏的。README 说得很明确：随模板发布，也理应随模板发布，因为模板本来就是给你改的。

内容分四块：

- `catalog.yaml`：74 个技能和 49 个角色的主登记表，记录覆盖率。
- `quality-rubric.md`：按类别的通过标准。
- `skills/`：每个技能一份行为规格，按 gate、review、authoring、readiness、pipeline、analysis、team、sprint、utility 分类。
- `agents/`：每个角色一份规格，按总监、主管、专家、引擎、运营、QA 分类。

驱动它的是两个技能：`/skill-test` 和 `/skill-improve`。

## 四种测试模式

`/skill-test` 有四个模式：

`static` 做七项结构检查，读技能文件，不运行技能。可以测单个，也可以 `all`。

`spec` 拿行为规格逐条评估技能或角色。比如 `gate-check` 的规格会检查它是否读取评审模式、是否在 solo 模式跳过全部门禁、是否禁止自动推进。

`category` 按类别标准评估。gate 类技能的关键指标是"读取评审模式、full/lean/solo 三种总监小组、不自动推进"。

`audit` 输出覆盖率全景：哪些技能有规格、上次测试时间、结果。

README 还给了一张"删掉 studio-tests 会怎样"的表：static 仍能跑，audit 退化为报告没有目录，spec 和 category 直接失效，`/skill-improve` 失去类别通过项。这张表是很好的依赖说明范例：说清每个模式的具体代价，而不是笼统说"会影响测试"。

## 静态检查的实测

`skill-lint.sh` 是 static 模式七项检查的脚本实现。在快照上对 `dev-story` 运行：

```
skills	1	.claude/skills
skill	dev-story	files=3	lines=389
check1	dev-story	frontmatter=ok	missing=-	name=match
check2	dev-story	phases=7	h2=11	h2_total=11
check3	dev-story	verdicts=FAIL:1,BLOCKED:6,COMPLETE:1	assessment_words=readiness
check4	dev-story	may_i_write=1	before_writing=0	approval=0	ask_write_lines=5	write_tools=Write,Edit
check5	dev-story	last_section=Phase 7: Summary, files, checkpoint	skills_named=story-done,dev-story,code-review,architecture-decision	next_phrases=6/5
check6	dev-story	context_fork=no	phases=7	h2=11
check7	dev-story	hint=[story-path]	args_section=-
checked	1 of 1
```

七项分别看：前置元数据完整、阶段数、判决词、写入前是否请求批准、最后一节是否指向下一步、是否设置独立上下文、参数提示。

对全部技能运行，最后一行是 `checked 74 of 74`。这个数字很重要：它证明脚本读到了全部 74 个，而不是读了 60 个然后报告完成。脚本头部专门说明，读不到的技能会打印 `NOT_READ`，且不计入已读，避免"没检查看起来像通过"。

注意脚本输出的定位：它只给事实，不给判决。`check3` 列出判决词出现次数，至于 `BLOCKED` 出现六次是否过多，由 `/skill-test` 判断。这符合 `CLAUDE.md` 里"辅助脚本只输出观察"的承重约定。

## 五条义务

`.claude/rules/skill-authoring.md` 是写技能和门禁时的核心规则，只有五条，但每条都指向同一类失败。

第一条：每个门禁判决都要有"无法评估"值。三态判决会把所有未知压成一个断言。排序要讲究：它必须高于通过，低于失败。

第二条：缺失值不能默认成宽松值。尤其在框架里没人写那个键的时候。先问谁设置它；一个有读无写的键，默认分支就是每个项目的实际行为。

第三条：跳过的步骤要自己说出来。在输出里说，不只写在源码注释里。

第四条：不要断言无法溯源的事实，并且把缺口接到判决上。只标记不接线，缺口就只是注释。

第五条：门禁要派生覆盖集，不要枚举。白名单会漏掉后来新增的技能。如果类别无法机械判定，就在门禁里说明原因并保留清单，同时记录扩展义务。

还有两条门禁细则：断言一个不可能偶然为真的东西，比如不要检查单词 "unity"，因为文件路径里可能包含它，而 "community" 也包含；以及"没亲眼见它失败过的门禁不算门禁"，要故意破坏一次，确认它失败，再恢复。

最后一条最容易被跳过。写了一个检查，跑一次显示通过，就以为它能工作。实际上它可能永远通过。仓库要求做一次变异测试：把被守护的东西改坏，看检查是否报警。

## 版本与升级

`project.yaml` 里有 `framework.version: 1.2.0` 和 `last_upgraded: 2026-10-19`。`UPGRADING.md` 描述从上游拉取更新的流程，`migrate-v1-config.sh` 处理旧配置迁移。

这套机制的风险在第 15 章讨论过：模板更新会带入可执行脚本。从工程角度，升级还需要三件事：

1. 升级前看 `.claude/hooks/` 和 `.claude/scripts/` 的 diff。
2. 升级后跑 `/skill-test static all`，确认 74 个技能都能读。
3. 跑一次真实的 `/dev-story` 或团队流水线，确认配置解析和行为规格没有漂移。

只有第一步是自动的。后两步需要真实项目。

## 这套验证覆盖不到什么

`skill-test` 的所有模式都只读文件，不运行技能。README 明确写了：每个模式都读文件，没有一个运行技能。所以它证明的是结构合规和规格存在，不是行为正确。

真正的行为验证需要真实会话。仓库在 `studio-tests/catalog.yaml` 里记录"上次规格测试"和"上次类别测试"的时间与结果，但这些记录也依赖人手动触发。

还有一类缺口：文档提到的根目录 `tests/` 在快照里不存在。`release-review` 文档说框架自己的测试套件覆盖了配置解析链，但这次克隆的仓库里没有那个目录。这不影响使用，但说明"有测试"和"测试在当前分发里"是两件事。读的时候要区分。

## 常见误解

误解一：`/skill-test static` 通过就说明技能能正常工作。它只检查结构，不执行技能。

误解二：规格测试是自动化的。它需要模型读规格、逐条判断，结果依赖模型的理解。

误解三：`studio-tests/` 是可选装饰。删掉它，spec 和 category 两个模式直接失效。

## 练习

1. 对任意一个技能运行 `skill-lint.sh`，解释七项检查各自的用途。
2. 为一个你写的门禁设计一条"无法评估"路径，并说明它在判决排序中的位置。
3. 选择一个现有检查，做一次变异测试：破坏它守护的对象，确认它失败，再恢复。

## 答案提示

1. 前置元数据完整性、阶段结构、判决词覆盖、写入前批准、结尾指向下一步、上下文隔离、参数提示。它们共同保证技能可被发现、可被执行、可被交接。
2. 例如"文件存在但无法读取"应返回 NOT ASSESSED，而不是通过或失败。它排在通过之上、失败之下，理由是无法评估没有建立良好证据，但已知失败更可操作。
3. 例如把一份 JSON 数据文件故意写坏，运行 `validate-commit.sh` 的对应路径，确认得到 `exit 2`；恢复文件再跑一次确认通过。
