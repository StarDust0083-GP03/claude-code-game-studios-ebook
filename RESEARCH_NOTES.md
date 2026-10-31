# 研究与写作记录

## 范围

对象：Donchitos/Claude-Code-Game-Studios。源码快照 `05ad7c8a5b8aa2aa86bbd3439ae7cf7295cac418`，framework.version 1.2.0，采集日期 2026-10-31。只做静态解读、隔离的脚本实验及阅读站检查；不声称运行 Claude Code 全流程或制作出游戏。

参考本地 `octop-architecture-ebook` 的问题驱动结构、Markdown 章节布局与静态阅读器。书稿独立撰写。模板为 MIT，保留阅读器来源说明和上游许可。

## 关键发现与证据

- 这是 Markdown/YAML/Bash 组合的工作流模板，运行宿主是 Claude Code；不是包含 49 个常驻进程的服务。证据：CLAUDE.md、.claude/agents、settings.json、coordination-rules.md。
- 实数 49 agent、74 SKILL.md、14 rule；hooks 目录有 18 个 .sh，但 README 宣称 15 hooks，包含未直接注册的辅助脚本时口径不同。模板目录实际有 71 个文件，README 表格的 62 不作为当前精确统计。
- 默认 rigor=minimal，展开六个配置；显式值优先，旧 review-mode.txt 也可能覆盖展开。证据：yaml-helper.sh 的 resolve_setting 与 expansion。
- validate-write 仅告警；validate-read 可 exit 2；validate-commit 的 JSON 数据检查有阻断，其余多为建议。不能把 hooks 一概叫安全沙箱。
- dev-story 不等于完成；story-done 不执行测试，证据存在不等于测试通过。证据：两份 SKILL.md。
- 通用 gameplay-programmer 要求测试，而 dev-story 在 qa.level=minimal 明确豁免 Logic/Integration 测试，存在宽泛角色规则与具体流程分支的张力。书中保留，不替上游掩盖。
- studio-tests 是框架行为规格，不等于本快照带有可执行 tests/ 套件。文档提到的 tests/ 在本次快照根目录不存在。

## 写作提纲与来源

0. 前言与事实边界：README、project.yaml。
1. 需求：CLAUDE.md、协作原则、coding-standards。
2. 总体架构：settings.json、directory-structure、context-management。
3. 入门路由：start/SKILL.md、project-state.sh。
4. 配置求值：config-resolution、yaml-helper.sh。
5. 角色：agent-roster、gameplay-programmer、model-tiers。
6. Skill 协议：dev-story、skill-authoring、config-resolution。
7. 产物模型：templates/story、tr-registry、ADR 模板。
8. 实施链路：dev-story、code-root-resolution。
9. 验收：story-done、review-receipts、run-and-observe。
10. Hook：settings.json、validate-read/write/commit。
11. 注册表：design/registry/entities.yaml、docs/registry/architecture.yaml、registry.sh。
12. 协作：team-combat、coordination-rules、error-recovery。
13. 引擎：code-root-resolution、engine-reference、dev-story。
14. 恢复：context-management、session-state.sh。
15. 安全：settings.json、automation-modes、validate-push。
16. 验证与演进：studio-tests/README、UPGRADING、skill-lint.sh。
17. 最小实验：本书原创 Python 模型及针对上游脚本的隔离实验。
附录：固定提交的逐文件来源清单与术语。

## 外部交叉核验

通过 Context7 `/websites/code_claude` 查询 Claude Code Hooks，确认 PreToolUse exit 2 阻断，exit 0 按正常权限流继续。官方入口 https://code.claude.com/docs/en/hooks 与 https://code.claude.com/docs/en/hooks-guide 。这是采集时官方语义的补充，不是对所有未来版本的兼容保证。

## 审校标准

区分源码规则、脚本执行结果和作者建议；保留未知与失败状态；不编造生产经历、模型费用或游戏运行截图。每章提供固定源码入口、具体案例、练习与答案提示。发布是用户明确要求的交付动作，采用新建独立公开仓库与 GitHub Pages，不修改已有同名 fork。
