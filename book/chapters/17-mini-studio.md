# 第 17 章 最小实验：用一百多行 Python 复刻四条约束

## 场景

读完十多万字的规则和几十个 Bash 脚本，很多机制仍然停留在"看懂了"的层面。要确认真的理解，最好的办法是用另一种语言把它重写一遍。

这一章给出一个 `examples/mini_studio.py`，约两百行，标准库，无依赖。它不复制上游脚本，只复刻四个决定行为走向的约束：配置解析、故事状态、验收判决、证据时效。配套 17 个单元测试，全部通过。

## 配置解析

模型里的 `resolve()` 接收三张表：项目配置、本地配置、遗留配置。

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

它保留了三个关键行为：

1. 本地配置只对白名单键生效。测试 `test_local_ignored_for_protected_key` 把 `qa.level` 同时写进两张表，断言结果来自项目配置。
2. 显式值优先于 rigor 展开。测试 `test_explicit_key_beats_rigor_expansion` 在 `rigor: full` 下显式写 `workflow: minimal`，断言 workflow 保持 minimal。
3. 非法枚举回落而不是胜出。测试 `test_invalid_enum_falls_through` 用 `rigor: strict`，断言 workflow 变成 minimal，并且备注里点名了非法值。

第三个行为最容易被写错。直觉写法是"读到就用"，但那样一个拼写错误会传播到所有技能，而错误配置往往比缺省配置更隐蔽。

## 代码根解析

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

三个测试覆盖三种情况：引擎优先、单一目录推断、两个候选目录时不猜。

第三个断言返回 `(None, "unresolved")`，而不是默认到 `src`。这是第 13 章那条规则的代码化：缺失值不能默认成宽松值。

## 故事状态与"跳过不是同意"

```python
def start(self):
    if self.status not in ("Ready", "Blocked"):
        return f"refused: {self.status} cannot start"
    if self.answer not in ("yes", "approved"):
        return "waiting: no explicit approval"
    self.status = "In Progress"
    return "started"
```

`answer` 模拟用户对"我可以开始吗"的回复。只有明确同意才推进，`None`、空字符串、`"skipped"` 都停在原地。

对应的测试是 `test_skipped_question_is_not_approval`：调用 `start()`，断言返回包含 `waiting`，且状态仍然是 `Ready`。

关闭也有守卫：`close()` 只在判决为 PASS 且状态是 In Progress 时生效。`test_no_close_on_unknown` 断言 UNKNOWN 判决被拒绝，状态保持 In Progress。

## 判决排序

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

四个测试覆盖：失败压过未知、未知压过通过、延期算"带备注的通过"、全部覆盖算通过。

`RANK` 在演示里没有直接用，它表达的是排序关系：FAIL 最高，UNKNOWN 次之，NOTES，PASS。这正是 `skill-authoring.md` 第一条义务要求的排序：无法评估要高于通过，低于失败。

## 证据时效

```python
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]

def evidence_state(stamp, paths):
    if not stamp:
        return ["RECEIPT_NONE"] + [f"NEW: {p}" for p in paths]
    ...
```

`receipt()` 给文件打内容哈希，`evidence_state()` 比对，输出五种状态：UNCHANGED、CHANGED、NEW、GONE、RECEIPT_NONE。

测试里创建临时文件、打回执、修改、删除，依次断言 UNCHANGED、CHANGED、GONE。另一个测试断言没有回执时第一行是 RECEIPT_NONE，而不是空列表。

最后一条很重要：没有回执时不能返回空结果，因为空结果会被读成"没有变化"。必须显式说"无法判断"。

## 编号不回收

```python
def next_id(kind, seen):
    nums = [int(x.rsplit("-", 1)[-1]) for x in seen if x.rsplit("-", 1)[-1].isdigit()]
    return f"{kind}-{max(nums, default=0) + 1:03d}"
```

测试给 `["story-001", "story-007"]`，断言结果是 `story-008`，不是 `story-002`。

这条规则的成本是编号会稀疏，收益是历史引用永远指向同一对象。

## 实际运行

```bash
$ cd examples
$ python3 -m unittest -v test_mini_studio.py
...
Ran 17 tests in 0.001s
OK

$ python3 mini_studio.py demo
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

输出本身就是一份行为清单。配置里 `review_mode` 来自本地文件，其余来自 standard 展开；非法 rigor 被忽略并回落到 minimal；两个候选目录被视为未解析；没有明确回答时故事不启动；UNKNOWN 不允许关闭；证据修改后被识别为过期。

## 与真实实现的差距

这个模型刻意简化了几件事：

- 上游用 Bash 和 awk 实现，为了在没有 Python 的环境里也能跑；模型直接用 Python。
- 上游的配置解析还处理旧版镜像、Tab 缩进、BOM、CRLF、重复块合并；模型只保留优先级和枚举回落。
- 上游的故事状态由技能流程维护，没有代码强制；模型把它写成了显式状态机，反而更严格。
- 上游的证据检查用 git hash-object 或 sha1sum；模型用 sha256，语义相同。

这些差距本身是练习材料。把任何一项补上，都会暴露新的边界情况。

## 练习

1. 给 `resolve()` 加旧版镜像支持，让 `review_mode` 可以从 `legacy` 表读到，并写一个测试断言优先级低于项目配置。
2. 给 `Story` 加 `Blocked` 状态和一条解除阻塞的路径，要求解除时必须有明确的用户回答。
3. 把 `evidence_state()` 扩展为支持目录参数，目录下的文件逐个比对，写测试覆盖新增文件和删除文件。

## 答案提示

1. 在循环里插入 `("legacy", legacy, None)` 一级，注意放在项目配置之后、展开之前；测试里同时写项目值和遗留值，断言来源是 `project.yaml`。
2. `unblock(reason)` 只在 `status == "Blocked"` 且 `answer` 是明确同意时转为 `Ready`，其余返回 `waiting`。
3. 用 `Path.rglob("*")` 展开目录，把相对路径作为键；新增文件报 NEW，回执里有但磁盘没有的报 GONE。测试可以用 `TemporaryDirectory` 创建两层结构。
