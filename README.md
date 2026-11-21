# Claude Code 游戏工作室：从一堆提示词到一条可验收的流水线

一本关于 [Donchitos/Claude-Code-Game-Studios](https://github.com/Donchitos/Claude-Code-Game-Studios)（CCGS）的大白话硬核源码解读。不吹不黑，沿着入口双轨、配置解析、产物门禁、Hook 防线和引擎/品类适配几条主线，把一套看起来像“49 个 AI 员工”的仓库拆回它真实的 Markdown、YAML 和 Bash 骨架。

全书锚定上游 **`v1.3.0`**（"Make me a game"）固定快照：commit `abc0de79d6ceb0b5d7aa693945849b3937afbe6a`（上游发布于 `2026-11-09`，采集于 `2026-11-21`）。书中严格区分源码写死的规则、脚本实跑逻辑和工程判断，不把静态源码研究冒充生产账单压测。

## 阅读与产物

- 在线阅读：<https://stardust0083-gp03.github.io/claude-code-game-studios-ebook/>
- `wiki/index.html`：分章目录、全文搜索、字号与深浅色主题切换。
- `wiki/book.html`：样式与脚本全部内联的离线合订本。
- `wiki/assets/diagrams/`：6 幅随主题换肤的内联 SVG 架构图，可打印、可进 EPUB。
- `exports/claude-code-game-studios.pdf`：A5 印刷规格 PDF。
- `exports/claude-code-game-studios.epub`：EPUB 3，19 个章节。
- `book/ClaudeCode游戏工作室.md`：合并书稿。
- `sources/UPSTREAM.md`：v1.3.0 上游快照与实测资产统计口径。

## 六幅内联 SVG 图

1. 四种约束：常驻上下文、按需加载、Hook、宿主权限
2. 配置解析链与非法枚举回落
3. `/dev-story` 的七个阶段与两道门禁
4. 四态判决的优先级
5. Hook 事件与真实阻断范围
6. `team.size` 的三档塌缩

## 这本书想回答的问题

1. 49 个 Agent、78 个 `SKILL.md`（75 正式 + 3 旧名兼容）、15 条注册 Hook、73 份品类资料到底怎么配合，哪些真有代码兜底、哪些全靠模型自觉？
2. v1.3.0 为什么把“先玩一把（`/prototype`）”扶正成主干道，把重流程收编为 Studio Mode，又怎么靠同种子回放把单文件原型安全 Grow 成 Vite + TypeScript 工程？
3. 一个 `modes.rigor` 怎么沿着 5 级瀑布展开成 6 个子开关？15 个本地可覆盖白名单键和非法枚举下落是怎么防呆的？
4. `/dev-story` 怎么靠代码根不瞎猜和触发器 0 管住写代码，`/story-done` 又怎么靠四态判决、内容哈希回执和 `Own calls` 堵死“基本完成”？
5. 15 条 Hook 里哪 3 处真的 `exit 2`？Windows 无 Git Bash 的双语包装、安全边界和 `studio-tests/` 的真实覆盖范围在哪？

## 目录

前言 + 17 章 + 附录（共 19 节）。每章从真实踩坑场景切入，指着具体源码和脚本拆机制，最后给出常见误解、终端练习与参考思路。书末第 17 章附约 209 行零依赖 Python 教学模型和 17 个单元测试，不用装 Claude Code 和游戏引擎也能亲手跑通核心约束。

## 本地构建与校验

```bash
./scripts/build.sh
```

或分步执行：

```bash
npm ci --prefix wiki
python3 scripts/make_diagrams.py   # 生成 wiki/assets/diagrams/*.svg
node wiki/build.mjs                 # 生成 wiki/index.html、章节页、搜索索引、book.html、合并书稿
python3 scripts/make_epub.py       # 生成 exports/*.epub
chromium --headless=new --disable-gpu --no-sandbox --no-pdf-header-footer \
  --print-to-pdf=exports/claude-code-game-studios.pdf wiki/book.html
python3 scripts/check_links.py     # 本地链接与导出文件检查
python3 -m unittest discover -s examples -v   # 17 tests
```

## 许可与致谢

本书文字与实验代码采用 MIT 许可。上游 CCGS 同样采用 MIT 许可，其仓库、文档与脚本版权归原作者 Donchitos 及贡献者所有。详见 `LICENSE` 与 `NOTICE`。
