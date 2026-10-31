#!/usr/bin/env python3
"""Generate the inline SVG diagrams used by the ebook.

The viewBox is sized to the A5 text column (~420pt) so labels stay readable in
print; on screen the same SVG scales up. Inline SVG keeps the figures themeable,
searchable by screen readers, and authoritative in EPUB without a JS runtime.
"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "wiki" / "assets" / "diagrams"
FONT = "'IBM Plex Sans','Noto Sans CJK SC',system-ui,sans-serif"
MONO = "'IBM Plex Mono','SFMono-Regular',Consolas,monospace"
W = 420


def t(x, y, s, size=9, weight=400, fill="var(--ink)", anchor="start", family=FONT, opacity=1):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" opacity="{opacity}">{escape(s)}</text>')


def box(x, y, w, h, title, lines=(), accent=False, title_size=11):
    stroke = "var(--amber)" if accent else "var(--line)"
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2.5" fill="var(--paper-2)" '
           f'stroke="{stroke}" stroke-width="{1.4 if accent else 0.8}"/>']
    out.append(t(x + 9, y + 17, title, title_size, 600))
    for i, line in enumerate(lines):
        out.append(t(x + 9, y + 32 + i * 13, line, 9, 400, "var(--muted)"))
    return "".join(out)


def badge(x, y, label, color="var(--forest)", w=58):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="16" rx="8" fill="none" stroke="{color}" stroke-width="0.9"/>'
            + t(x + w / 2, y + 11.5, label, 8.8, 600, color, "middle"))


def arrow(x1, y1, x2, y2, dashed=False, color="var(--muted)"):
    dash = ' stroke-dasharray="4 3"' if dashed else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1.1"'
            f'{dash} marker-end="url(#arrow)"/>')


def svg(height, title, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" width="{W}" height="{height}" role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--muted)"/></marker></defs>
{body}
</svg>'''


def four_layers():
    b = [t(8, 10, "强制力递增", 8.2, 600, "var(--muted)")]
    rows = [
        ("常驻上下文", "CLAUDE.md 与 @ 导入的规则", "模型看得见，可以忽略", "建议"),
        ("按需加载", "SKILL.md、参考文档、Agent 提示词", "范围更窄，仍是文字", "较软"),
        ("Hook 回调", "settings.json 注册 15 条命令", "部分事件 exit 2 才阻断", "部分"),
        ("宿主权限", "permissions.deny 命令模式", "宿主执行，不靠模型配合", "强制"),
    ]
    for i, (title, sample, note, level) in enumerate(rows):
        y = 20 + i * 64
        b.append(box(8, y, 214, 54, title, [sample], accent=(i == 3)))
        b.append(t(232, y + 24, note, 9, 400, "var(--muted)"))
        b.append(badge(350, y + 19, level, "var(--forest)" if i == 3 else "var(--muted)"))
    return svg(286, "四种约束：从建议到强制", "".join(b))


def config_chain():
    b = [t(8, 10, "第一个合法值胜出；非法枚举继续下落", 8.2, 600, "var(--muted)")]
    cards = [
        ("project.local.yaml", "仅白名单：review_mode / team.size", True),
        ("project.yaml", "显式值优先于落盘镜像", False),
        ("legacy 镜像", "review-mode.txt / production/stage.txt", False),
        ("rigor 展开", "六个子设置；显式值继续压过展开", False),
        ("末端默认", "minimal / collaborative", False),
    ]
    for i, (title, note, accent) in enumerate(cards):
        y = 22 + i * 56
        b.append(box(8, y, 404, 44, title, [note], accent=accent, title_size=10))
        if i < len(cards) - 1:
            b.append(arrow(210, y + 44, 210, y + 56, color="var(--line)"))
    b.append(t(8, 322, "输出值和来源：project.yaml / rigor:standard / default", 9, 400, "var(--muted)"))
    b.append(t(8, 338, "读白名单必须等于 /settings --local 的写白名单", 9, 400, "var(--amber)"))
    return svg(350, "配置解析链", "".join(b))


def dev_story():
    b = []
    phases = [
        ("1", "故事与档位", "story-facts.sh；按 GDD 解析 system_overrides"),
        ("2", "前置检查", "需求表、ADR、控制清单、依赖故事"),
        ("3", "标记进行中", "只问一次；拒绝则不改状态继续"),
        ("4", "选择执行者", "按 Layer 与 Type 选程序员，再选引擎专家"),
        ("5", "简报派活", "给路径和要点，不粘贴整份文档"),
        ("6", "产物与运行", "文件存在 → 测试存在 → 解析 → 截图观察"),
        ("7", "总结与检查点", "实际文件写入 ## Files，收尾三行"),
    ]
    for i, (num, title, note) in enumerate(phases):
        y = 10 + i * 50
        b.append(f'<circle cx="18" cy="{y + 20}" r="12" fill="var(--paper-2)" stroke="var(--forest)" stroke-width="0.9"/>'
                 + t(18, y + 23.5, num, 9, 600, "var(--forest)", "middle"))
        b.append(box(38, y, 374, 38, title, [note], accent=(i in (1, 5)), title_size=10))
        if i < len(phases) - 1:
            b.append(arrow(18, y + 32, 18, y + 50, color="var(--line)"))
    b.append(t(8, 372, "P2 不通过：写 BLOCKED 检查点，不派代理。P6：报告不算完成，文件才算。", 9, 400, "var(--amber)"))
    return svg(384, "dev-story 的七个阶段", "".join(b))


def verdict_order():
    b = [t(8, 10, "排序：失败 > 无法评估 > 带备注通过 > 通过", 8.4, 600, "var(--ink)")]
    rows = [
        ("FAIL", "某条验收失败，或存在阻断级缺口", "BLOCKED", "var(--amber)"),
        ("UNKNOWN", "无法评估：没说清、还没测、输入缺失", "NOT ASSESSED", "var(--forest)"),
        ("PASS_WITH_NOTES", "全部通过或延期，但有建议级事项", "COMPLETE WITH NOTES", "var(--muted)"),
        ("PASS", "全部通过，没有建议级事项", "COMPLETE", "var(--forest)"),
    ]
    for i, (word, note, label, color) in enumerate(rows):
        y = 22 + i * 50
        b.append(f'<rect x="8" y="{y}" width="404" height="40" rx="2.5" fill="var(--paper-2)" '
                 f'stroke="{color}" stroke-width="{1.3 if i < 2 else 0.8}"/>')
        b.append(t(18, y + 16, word, 9, 700, color, family=MONO))
        b.append(t(18, y + 30, note, 9, 400, "var(--muted)"))
        b.append(t(402, y + 24, label, 9.2, 600, color, "end"))
    b.append(t(8, 238, "无法评估高于通过，低于失败；信息行不会把 COMPLETE 降级。", 9, 400, "var(--muted)"))
    return svg(250, "四态判决的优先级", "".join(b))


def hook_map():
    b = []
    rows = [
        ("SessionStart", "session-start · detect-gaps", "记录", "var(--muted)"),
        ("PreToolUse Read", "validate-read", "阻断", "var(--forest)"),
        ("PreToolUse Write", "validate-registry · validate-write", "提醒", "var(--amber)"),
        ("PreToolUse Bash", "validate-commit · validate-push", "窄阻断", "var(--amber)"),
        ("PostToolUse Write", "validate-assets · validate-skill", "反馈", "var(--forest)"),
        ("PreCompact / Stop", "pre-compact · session-stop", "记录", "var(--muted)"),
        ("Subagent Start/Stop", "log-agent* · validate-agent-artifact", "记录/提醒", "var(--muted)"),
    ]
    for i, (event, scripts, effect, color) in enumerate(rows):
        y = 12 + i * 48
        b.append(t(8, y + 16, event, 9, 600, "var(--ink)"))
        b.append(t(112, y + 16, scripts, 8.4, 400, "var(--muted)"))
        b.append(badge(346, y + 4, effect, color))
        b.append(f'<line x1="8" y1="{y + 26}" x2="412" y2="{y + 26}" stroke="var(--line)" stroke-width="0.6"/>')
    b.append(t(8, 362, "15 条注册命令；硬阻断只有 validate-read。", 9, 400, "var(--muted)"))
    return svg(374, "Hook 事件与效果", "".join(b))


def team_collapse():
    b = []
    rows = [
        ("individual", "默认", ["gameplay-programmer"], "正文点名 7 个，实际派生 1 个", True),
        ("small", "提高档位", ["game-designer · gameplay-programmer · ai-programmer",
                              "technical-artist · sound-designer · specialist · qa-tester"], "完整流水线", False),
        ("studio", "完整档位", ["以上全部 · 引擎子专家", "再加一轮对抗性评审"], "验证与对抗", False),
    ]
    for i, (name, tag, chips, note, accent) in enumerate(rows):
        y = 10 + i * 84
        b.append(f'<rect x="8" y="{y}" width="404" height="72" rx="3" fill="none" '
                 f'stroke="{"var(--forest)" if accent else "var(--line)"}" stroke-width="{1.4 if accent else 0.8}"/>')
        b.append(t(18, y + 18, name, 10, 700, "var(--ink)", family=MONO))
        b.append(badge(330, y + 4, tag, "var(--forest)" if accent else "var(--muted)", 78))
        for j, chip in enumerate(chips):
            b.append(t(18, y + 36 + j * 14, chip, 9, 400, "var(--ink)"))
        b.append(t(18, y + 64, note, 8.5, 400, "var(--muted)"))
    b.append(t(8, 284, "收窄必须显式声明 Active set，避免把配置收窄误读成故障。", 9, 400, "var(--muted)"))
    return svg(296, "team.size 的三种塌缩", "".join(b))


DIAGRAMS = {
    "four-layers": four_layers,
    "config-chain": config_chain,
    "dev-story": dev_story,
    "verdict-order": verdict_order,
    "hook-map": hook_map,
    "team-collapse": team_collapse,
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in DIAGRAMS.items():
        path = OUT / f"{name}.svg"
        path.write_text(fn(), encoding="utf-8")
        print(f"wrote {path.relative_to(OUT.parent.parent.parent)}")


if __name__ == "__main__":
    main()
