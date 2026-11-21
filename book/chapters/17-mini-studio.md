# 第 17 章 最小实验：用两百行 Python 亲手跑通四条核心约束

## 场景：纸上看懂不算数，换门语言写一遍才真算摸透

前面十六章拆了几十个脚本和上百条规则，光靠眼睛看，很容易产生“我都懂了”的错觉。验证自己到底有没有吃透一套工作流框架，最硬核的办法就是**脱离 Claude Code、脱离游戏引擎，用自己顺手的语言把最值钱的几条约束从头复刻一遍，再写单元测试把边界全捅一遍**。

本书配套的 `examples/mini_studio.py` 就是这么一个零依赖教学模型（约 209 行纯 Python 标准库），外加 `examples/test_mini_studio.py` 里的 **17 个单元测试**。它不是要把几千行 Bash 脚本照抄成 Python，而是专门拎出决定 CCGS 靠谱程度的五根硬骨头亲手跑一遍：

1. 配置优先级瀑布与非法枚举下落；
2. 代码根不瞎猜（歧义直接报未解析）；
3. 故事显式状态转移与“跳过提问不等于同意”；
4. 四态判决排序（未知压过通过，失败压过一切）；
5. 内容哈希证据回执与注册表 ID 永不回收。

## 约束一：配置解析与非法枚举下落

模型里的 `resolve()` 接三张字典——`project`、`local`、`legacy`——严格按瀑布顺序往下找第一个合法值：

```python
def resolve(project, local=None, legacy=None):
    ...
    for key in sorted(keys):
        for source, table, allowed in (("project.local.yaml", local, LOCAL_KEYS),
                                       ("project.yaml", project, None),
                                       ("legacy", legacy, None)):
            if allowed is not None and key not in allowed:
                continue
            if key in table:
                if _valid(key, table[key]):
                    out[key] = (table[key], source)
                    break
                notes.append(f"{key}: '{table[key]}' is not a valid enum value; ignored")
        else:
            # rigor expansion, then documented default
```

四个单元测试钉死了最容易写歪的角落：
- `test_local_wins_for_whitelisted_key`：白名单里的 `modes.review_mode` 本地优先；
- `test_local_ignored_for_protected_key`：锁死键 `qa.level` 就算写进 `local` 也被无视，乖乖走 `project.yaml`；
- `test_explicit_key_beats_rigor_expansion`：`rigor: full` 下显式钉死 `modes.workflow: minimal`，展开不准盖掉它；
- `test_invalid_enum_falls_through`：手滑写了 `modes.rigor: strict`，不报错崩掉也不拿 `strict` 硬用，而是记进 `_notes` 后回落到 `minimal`。

## 约束二：代码根解析，有歧义就坚决不猜

```python
def resolve_code_root(engine, dirs):
    by_engine = {"godot": "src", "unity": "Assets", "unreal": "Source"}
    if engine in by_engine:
        return by_engine[engine], "engine.name"
    candidates = [d for d in ("src", "Assets", "Source") if d in dirs]
    if len(candidates) == 1:
        return candidates[0], "detected"
    return None, "unresolved"
```

三个测试覆盖了三条路径：设了引擎就听引擎的、没设引擎且目录里只有一个候选根才推断、同时出现 `src` 和 `Assets` 时直接吐 `(None, "unresolved")`，绝不偷懒默认返回 `src`。

## 约束三：状态流转与“跳过不等于同意”

```python
def start(self):
    if self.status not in ("Ready", "Blocked"):
        return f"refused: {self.status} cannot start"
    if self.answer not in ("yes", "approved"):
        return "waiting: no explicit approval"
    self.status = "In Progress"
    return "started"
```

只有用户明确给出 `"yes"` 或 `"approved"` 才允许把故事推进到 `In Progress`；`None`、空字符串、或者弹窗被关掉返回的 `"skipped"` 统统原地踏步（`test_skipped_question_is_not_approval`）。同样，关故事时 `close()` 绝不接受 `UNKNOWN` 判决（`test_no_close_on_unknown`），必须全绿 `PASS` 且处于进行中状态才放行。

## 约束四：四态判决排序

```python
PASS, NOTES, UNKNOWN, FAIL = "PASS", "PASS_WITH_NOTES", "UNKNOWN", "FAIL"
RANK = {FAIL: 3, UNKNOWN: 2, NOTES: 1, PASS: 0}

def verdict(criteria):
    states = {state for _, state in criteria}
    if "FAILS" in states:
        return FAIL
    if "UNTESTED" in states:
        return UNKNOWN
    if "DEFERRED" in states:
        return NOTES
    return PASS
```

逻辑短到只有 8 行，但三个单测直接锁死了整套验收门禁的灵魂：`FAIL` 压过 `UNKNOWN`，`UNKNOWN` 压过 `PASS`，只有合理延期 `DEFERRED` 才落进 `PASS_WITH_NOTES`。

## 约束五：内容哈希回执与编号不回收

```python
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]

def evidence_state(stamp, paths):
    if not stamp:
        return ["RECEIPT_NONE"] + [f"NEW: {p}" for p in paths]
    ...

def next_id(kind, seen):
    nums = [int(x.rsplit("-", 1)[-1]) for x in seen if x.rsplit("-", 1)[-1].isdigit()]
    return f"{kind}-{max(nums, default=0) + 1:03d}"
```

测试里在临时目录建一个 `combat.gd`、打完回执先测 `UNCHANGED`，往文件里多写一行立刻报 `CHANGED`，删掉文件立刻报 `GONE`；连“压根没有回执”也单独测了必须吐 `RECEIPT_NONE`，绝不返回空列表冒充“没变化”。编号生成器面对 `["story-001", "story-007"]` 铁定发 `story-008`，绝不捡漏回收 `story-002`。另外还有 `test_always_ask_survives_autonomous`，验证哪怕切到 `autonomous`，撞上 `file_deletions` 依然必须停下来问人。

## 直接在本机跑一遍

```bash
cd examples
python3 -m unittest -v test_mini_studio.py
# Ran 17 tests in 0.001s
# OK

python3 mini_studio.py demo
```

演示输出把所有机制摊在一屏里：

```text
config: {'docs.density': ('balanced', 'rigor:standard'), ...,
         'modes.review_mode': ('solo', 'project.local.yaml'), ...}
invalid enum: ('minimal', 'rigor:minimal')
code root: ('Assets', 'engine.name')
code root ambiguous: (None, 'unresolved')
start without answer: waiting: no explicit approval
start with answer: started
close on UNKNOWN: refused: verdict=UNKNOWN status=In Progress
close on PASS: closed
verdict mixed: PASS_WITH_NOTES
verdict untested: UNKNOWN
evidence fresh: ['UNCHANGED: /tmp/.../combat.gd']
evidence stale: ['CHANGED: /tmp/.../combat.gd']
ids: story-008
```

## 教学模型故意简化了什么（以及怎么把它升级到 v1.3.0）

为了把代码压在两百行以内让你一眼看完，这份教学模型刻意省掉了上游 v1.3.0 里不少实战细节，而这些差距刚好是最好的动手练手题：

- **运行环境与解析器**：上游用 Bash + awk（部分调 Python 3）扛住了 macOS 老 Bash 3.2、Windows CRLF、UTF-8 BOM、Tab 缩进报错、重复块合并、块标量跳过；模型直接用 Python 字典跳过文本解析。
- **v1.3.0 引擎表与自定义根**：上游已经在 `.claude/engines/engines.tsv` 里加上了 `Web` 引擎，并在第 0 步支持 `engine.code_root`（含 `.` 根目录和“非法不回退”）；模型里的 `resolve_code_root` 目前只写了三家引擎，还没加自定义根校验。
- **完整本地白名单**：上游 `yaml-helper.sh` 的本地白名单有 15 个键；模型只示范了 `rigor` 族里的 2 个核心键。
- **v1.3.0 的 `Own calls` 与同种子回放**：模型里的 `verdict()` 还没把“有未确认的 AI 自主拍板项”和“同种子回放 `CHANGED, not accepted`”接进 `FAIL` / `UNKNOWN` 门禁。
- **故事状态机**：上游全靠技能纪律约束，模型反而用代码写成了更硬的显式状态机。

## 练习

1. 给 `examples/mini_studio.py` 的 `resolve_code_root()` 加上 v1.3.0 的 `web` 引擎和可选参数 `custom_root`（支持 `.`，若目录不存在或含 `..` 或指向 `.claude`/`docs` 则直接返回 `(None, "invalid")` 且不回退到引擎默认），并补 3 个单元测试。
2. 扩展 `verdict()`，增加 `own_calls` 参数（每条带状态 `kept` / `change_requested` / `unanswered`）：只要有任何 `change_requested` 直接判 `FAIL`，有 `unanswered` 最高判 `UNKNOWN`，写测试验证优先级。
3. 给 `Story` 增加 `Blocked` 状态的解锁方法 `unblock(answer)`，要求同样严格遵守“跳过不等于同意”，只有明确批准才回到 `Ready`。

## 答案提示

1. 在 `by_engine` 里补 `"web": "src"`；函数开头先判断 `custom_root`：如果不为空，校验非绝对路径、不含 `..`、不在框架保留目录集合中且存在于 `dirs`（或等于 `.`），不合法立刻 `return None, "invalid"`，切记不要 `continue` 到下面的引擎映射。
2. 把 `change_requested` 并入 `FAIL` 分支判断，把 `unanswered` 并入 `UNKNOWN` 分支判断，即可复现 v1.3.0 `/story-done` Phase 5 和 Phase 7 的真实优先级。
3. `if self.status != "Blocked": return "refused..."`；`if answer not in ("yes", "approved"): return "waiting..."`；通过后将 `self.status = "Ready"` 并返回 `"unblocked"`。
