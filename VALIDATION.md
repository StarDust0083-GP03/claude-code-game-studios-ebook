# 验证记录

采集与写作日期：2026-10-31。上游快照 `05ad7c8a5b8aa2aa86bbd3439ae7cf7295cac418`。

## 本书构建

| 检查 | 命令 | 结果 |
|---|---|---|
| 阅读站构建 | `node wiki/build.mjs` | `Built 19 chapters, index, search, and book.html` |
| 图表生成 | `python3 scripts/make_diagrams.py` | 6 幅 SVG，全部通过 XML 解析 |
| 图表渲染 | 浏览器检查 | 6 幅内联 SVG，文字未越出 viewBox，文字两两无重叠；深色主题填充正确 |
| 图表审查 | 位图预览 + 版面检查 | 修正 Hook 阻断表述、判决配色语义，补充颜色与门禁图例 |
| 本地链接与导出 | `python3 scripts/check_links.py` | `OK: 22 pages, all local links and exports resolve` |
| 教学模型测试 | `python3 -m unittest discover -s examples -v` | `Ran 17 tests ... OK` |
| PDF | headless Chromium `--print-to-pdf` | 144 页，A5，约 3.5 MB，图表文字可提取 |
| EPUB | `python3 scripts/make_epub.py` | 19 个章节，6 幅 SVG 内联，XML 全部可解析 |

## 上游脚本实验

以下命令在上游克隆内只读执行，回执演示写入临时目录。

`project-state.sh` 在未配置模板上的关键行：

```
engine	-	unset
code_root	src	detected
source_files	0	src
concept	-	absent
gdd_files	0	design/gdd/*.md
adr	0	docs/architecture/adr-*.md
stage	-	unset
phase_inferred	concept	nothing
```

`yaml-helper.sh resolve_config` 的默认结果：

```
rigor: minimal (default)
review_mode: solo (rigor:minimal)
automation: collaborative (default)
workflow: minimal (rigor:minimal)
docs.density: terse (rigor:minimal)
story_granularity: coarse (rigor:minimal)
qa.level: minimal (rigor:minimal)
team.size: individual (rigor:minimal)
```

`registry.sh validate`：三份注册表均读到 0 条目，duplicate、tr_unknown、path_missing、status、layout 全为 0。

`skill-lint.sh dev-story`：7 项结构检查输出；`skill-lint.sh all` 最后一行 `checked 74 of 74`。

`review-receipts.sh`：未修改时 `UNCHANGED`，追加内容后 `CHANGED`；没有回执时 `RECEIPT: NONE`。

## 外部语义核对

通过 Context7 查询 Claude Code 官方文档 `/websites/code_claude`，确认：

- `PreToolUse` 的 `exit 2` 阻断工具调用，stderr 作为阻断原因反馈给模型。
- `PostToolUse` 的 `exit 2` 不能撤销已发生的操作，只把 stderr 交给模型作为修复反馈。
- 其他非零退出码属于非阻断错误。
- `exit 0` 且输出合法 JSON 时，JSON 字段生效。

官方入口：<https://code.claude.com/docs/en/hooks>、<https://code.claude.com/docs/en/hooks-guide>。Hook 语义随版本调整，移植前应以当前版本文档为准。

## 未做的验证

- 没有用 Claude Code 完整开发一款游戏。
- 没有统计 token 成本、模型质量或并行代理冲突率。
- 没有在 Unity 或 Unreal 项目上端到端运行。
- 上游文档提到的框架自有 `tests/` 目录不在此快照中，本书没有声称运行过它。
