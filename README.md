# Claude Code 游戏工作室：从一堆提示词到一条可验收的流水线

一本关于 [Donchitos/Claude-Code-Game-Studios](https://github.com/Donchitos/Claude-Code-Game-Studios)（CCGS）的中文源码解读。参考本地 SAM 系列电子书的讲法：先问这套流程为什么存在，再沿配置、产物、Hook 和验收四条线对照源码。

对象是固定快照 `05ad7c8`，框架版本 1.2.0，采集于 2026-10-31。书中区分三类证据：源码里写死的规则、脚本实际运行的结果、作者自己的判断。没有把静态阅读冒充成完整游戏开发或生产压测。

## 阅读

- 在线阅读：<https://stardust0083-gp03.github.io/claude-code-game-studios-ebook/>
- `wiki/index.html`：分章目录、搜索、字号与主题切换。
- `wiki/book.html`：内嵌样式与脚本的离线合订本。
- `exports/claude-code-game-studios.pdf`：A5，139 页。
- `exports/claude-code-game-studios.epub`：EPUB 3，19 个章节。
- `book/ClaudeCode游戏工作室.md`：合并书稿。
- `RESEARCH_NOTES.md`：提纲、来源与争议点。
- `sources/UPSTREAM.md`：上游快照与统计口径。

## 这本书想回答的问题

1. 49 个 Agent、74 个技能、15 个 Hook 到底怎么协作，哪些只是提示词？
2. 一个 `modes.rigor` 如何解析成六个设置，为什么显式写死会锁住档位？
3. `/dev-story` 怎样把故事变成代码，`/story-done` 又怎样拒绝"基本完成"？
4. 哪些 Hook 真的能拦住操作，哪些只发警告，权限层与 Hook 层的边界在哪？
5. 要给自己项目搭类似流程，哪几个部件值得抄，哪几个可以删？

## 目录

前言、17 章和附录。每章有固定结构：场景、源码入口、机制拆解、常见误解、练习与答案提示。

从 `/start` 的扫描、rigor 推断，到配置解析链、角色分层、Skill 的七段流程、故事与注册表、实施与验收、Hook 的退出码、团队流水线的塌缩、引擎代码根、上下文恢复、安全边界、静态验证，最后用一百多行 Python 复刻四条核心约束并跑 17 个单元测试。

## 本地构建

```bash
npm ci --prefix wiki
node wiki/build.mjs                 # 生成 wiki/index.html、章节页、搜索索引、book.html
python3 scripts/make_epub.py       # 生成 exports/*.epub
chromium --headless=new --no-sandbox --no-pdf-header-footer \
  --print-to-pdf=exports/claude-code-game-studios.pdf wiki/book.html
python3 -m unittest discover -s examples -v
```

阅读站是纯静态文件，无运行时依赖。`wiki/assets/` 下的阅读器样式与脚本沿用本地电子书项目，构建脚本按本书的 19 个章节改编。

## 验证

```bash
python3 -m unittest discover -s examples -v   # 17 tests
node wiki/build.mjs                            # 必须输出 Built 19 chapters
python3 scripts/check_links.py                    # 本地链接与资源检查
```

`examples/mini_studio.py` 是教学模型，不是上游脚本的移植。它保留配置优先级、非法枚举回落、代码根未解析、跳过不等于同意、判决四态、证据哈希过期、编号不回收这些行为。

## 许可与致谢

本书文字与实验代码采用 MIT 许可。上游 CCGS 同样采用 MIT 许可，其仓库、文档与脚本版权归原作者 Donchitos 及贡献者所有。书中引用的上游文件名、命令和输出用于评论与技术分析，阅读器样式参考本地电子书项目。详见 `LICENSE` 与 `NOTICE`。
