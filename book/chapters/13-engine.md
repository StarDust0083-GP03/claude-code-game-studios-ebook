# 第 13 章 引擎适配：代码根不是一个常量

## 场景

同一条 `/dev-story` 命令，在三个项目里要写三个不同的目录：

- Godot 项目，代码写 `src/`。
- Unity 项目，代码写 `Assets/`。
- Unreal 项目，代码写 `Source/<Module>/`。

写错了不会报错。Unity 只编译 `Assets/` 和 `Packages/`，写到 `src/` 的代码在编辑器里根本不存在。Unreal 只从 `Source/` 发现模块，别处的文件不参与构建。Godot 没有这个限制，因为 `res://` 覆盖整个项目根。

这一章讲仓库如何把"引擎"从一个提示词变量变成一组可解析的路径和规则。

## 解析顺序

`code-root-resolution.md` 定义了四步：

1. 从 `project.local.yaml`、`project.yaml` 读 `engine.name`。
2. 读旧版镜像 `.claude/docs/technical-preferences.md` 的 `Engine:` 行，`[TO BE CONFIGURED]` 不算值。
3. 从目录推断，但只在无歧义时：`src/`、`Assets/`、`Source/` 恰好存在一个。
4. 否则未解析。

第三步有两个陷阱。第一，Windows 和默认 macOS 的文件系统不区分大小写，测试 `Assets/` 是否存在时，Godot 项目里的小写 `assets/` 也会命中。所以比较必须按目录列表里的实际拼写。第二，同时存在两个候选根时不要猜，猜错会扫一半代码然后报告干净。

第四步是最重要的：未解析时**不默认到 `src/`**。文档把这条写成整个文件存在的理由，并引用了 `skill-authoring.md` 的第二条义务：缺失值不能默认成宽松的那个。

对读取和扫描，未解析时报告 `NOT ASSESSED — code root unresolved`，说明哪个检查没跑。对写入，直接不写。

## 为什么一条 grep 会骗人

假设 `validate-commit.sh` 里有一行 `grep -E '^src/gameplay/'` 用来找硬编码数值。在 Godot 项目里它正常工作。在 Unity 项目里它什么都匹配不到。

匹配不到的输出是什么？没有警告。提交成功。看起来一切干净。

这就是文档反复说的"零命中与干净结果不可区分"。仓库在多个地方记录了同一个 bug 的变体：`/security-audit` 的 Godot 专用 grep 在 Unity/Unreal 上返回零命中，被读成通过；本地化检查找不到硬编码字符串；内容审计数不到已实现内容；阶段检测数不到源文件，把完成的项目当成全新项目。

修法不是给每条 grep 加一个引擎分支，而是把代码根解析集中到一个函数 `resolve_code_root()`，让 Hook 和技能共用同一套语义。这样 Hook 和技能不会对"代码在哪"产生分歧。

## 引擎知识快照

`docs/engine-reference/` 是另一层适配。它解决的问题不是路径，是模型的知识截止日期。

目录结构固定：

```
<engine>/
├── VERSION.md              # 钉住的版本、验证日期、知识缺口窗口
├── breaking-changes.md     # 版本间的破坏性变更，按风险分级
├── deprecated-apis.md      # "不要用 X，用 Y" 对照表
├── current-best-practices.md
└── modules/                # 每个子系统一份速查，控制在 150 行内
```

Godot 的 `VERSION.md` 写着：引擎版本 4.7，项目钉住日期 2026-10-17，文档最后验证 2026-10-17，模型知识截止 2025 年 5 月。知识缺口警告说：训练数据大概覆盖到 4.3，4.5、4.6、4.7 在截止之后发布，引入了模型不知道的变化。

这份文件还记录了一个反向缺口，值得注意：

> 上面的警告是单向的，只说模型知道得比这个钉住版本少。反向缺口是真实存在的，而且 `/setup-engine` 的第 3 步会故意制造它（"钉新版本，之后再升级"）：参考资料可能超前于本机安装的编辑器，代理正确引用它，却生成本地编译不过的 API。信任带版本号的结论前，先看 `Installed at pin time`。`NOT DETERMINED` 意思是缺口未知，不是没有缺口。

这个区分很细：参考资料新于模型，是模型该查文档；编辑器旧于参考资料，是本地环境该升级。两种缺口的修法完全不同。

## 引擎专家

`project.yaml` 的 `specialists` 块有四个槽位：`primary`、`code`、`shader`、`ui`，外加 `additional`。

`primary` 从引擎名来：Godot 对应 `godot-specialist`，Unity 对应 `unity-specialist`，Unreal 对应 `unreal-specialist`。

`code` 是语言专家。这个槽位存在的理由是：`engine.name: Godot` 无法区分 GDScript 和 C#，而两者的写法差别很大。`/setup-engine` 会写入 `godot-csharp-specialist` 或 `godot-gdscript-specialist`。

`shader` 和 `ui` 按故事内容触发。`/dev-story` 在选择专家时，只在故事涉及着色器或材质时才带上 shader 槽位，只在 UI 故事里带上 ui 槽位。

所有槽位都是 `unset` 且没有 `primary` 时，技能说"未配置引擎专家"，然后继续，不阻塞。这是一个合理的降级：没有专家不等于不能写代码，只是少一层校验。

## 解析检查的引擎差异

`/dev-story` 对 Godot 给了完整命令，对其他引擎指向 `references/engine-checks.md`。Godot 的检查分两步：

```bash
godot --headless --path . --import
godot --headless --path . -s res://.claude/scripts/godot-parse-check.gd -- res://<each changed .gd>
```

第一条导入资源，第二条逐个检查脚本能否加载。退出码 1 表示有脚本没加载，输出里的 `PARSE FAIL:` 点名是哪个。

技能明确禁止两件事：用 `--check-only` 代替，以及只跑 `--import` 就声称做过解析检查。两条都指向同一个失败模式：一个看起来跑了、实际没验证的检查。

没有引擎可执行文件时，结果写 `parse NOT VERIFIED — engine binary not available`。不许读代码推断"应该能解析"。

## 测试根也跟着引擎走

同一个坑出现在测试上：

| 引擎 | 测试根 | 放错地方的结果 |
|---|---|---|
| Godot | `tests/unit/`、`tests/integration/` | 不运行 |
| Unity | `Assets/Tests/EditMode/`、`PlayMode/` | 测试运行器显示 "0 tests, Passed" |
| Unreal | `Source/<Module>/Private/Tests/` | "No automation tests matched" |

Unity 那一行尤其危险。`0 tests, Passed` 是一个绿色的成功信息，容易被当成通过。实际是测试文件没被编译，一条都没跑。

## 常见误解

误解一：代码根永远是 `src/`。它只是 Godot 那一行。

误解二：参考资料越新越好。参考资料新于本机编辑器时，会生成编译不过的代码。

误解三：引擎专家只影响提示词措辞。它决定审查哪些 API、用哪套惯例、检查哪些文件扩展名。

## 练习

1. 在副本里同时创建 `src/` 和 `Assets/`，运行 `project-state.sh`，观察 `code_root` 的来源和值。
2. 解释为什么 Unity 项目里把测试放到 `tests/` 会得到"0 tests, Passed"，这个结果为什么比报错更危险。
3. 假设模型建议了一个 Godot 4.7 的 API，而本机装的是 4.4，按仓库的做法应该怎么处理？

## 答案提示

1. 两个候选根同时存在属于有歧义，解析应返回未解析，`code_root` 一行会显示空值或 `unset` 来源，而不是任选一个。
2. Unity 只编译 `Assets/` 下的测试程序集，别处的文件不参与编译。运行器没有测试可跑，就报告零测试并通过。报错至少会让人注意，绿色通过会让人以为验证过了。
3. 先查 `docs/engine-reference/godot/VERSION.md` 的 `Installed at pin time` 和 `Knowledge Gap Warning`，标记该 API 为待验证，对照官方文档确认它在 4.4 是否存在，不确定就标 NOT SOURCEABLE 而不是照写。
