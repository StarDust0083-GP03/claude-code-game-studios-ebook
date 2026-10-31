"""A small, dependency-free model of four CCGS rules.

This is a teaching model, not a port of the upstream scripts. It reproduces the
shapes that make the framework work:

1. settings resolve local -> project -> rigor expansion -> default, and an
   invalid enum falls through instead of winning;
2. story status transitions are explicit, and a skipped answer is not a yes;
3. a verdict has four values, and UNKNOWN outranks PASS but not FAIL;
4. evidence carries a content hash, so stale evidence is detected;
5. registry ids are never reused.

Run `python3 mini_studio.py demo` or `python3 -m unittest -v test_mini_studio.py`.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

DEFAULTS = {"modes.rigor": "minimal", "modes.automation": "collaborative"}
LOCAL_KEYS = {"modes.review_mode", "team.size"}
ENUMS = {
    "modes.rigor": {"minimal", "standard", "full"},
    "modes.workflow": {"minimal", "standard", "full"},
    "modes.review_mode": {"full", "lean", "solo"},
    "qa.level": {"minimal", "standard", "full"},
    "team.size": {"individual", "small", "studio"},
    "docs.density": {"terse", "balanced", "thorough"},
    "modes.story_granularity": {"coarse", "balanced", "fine"},
    "modes.automation": {"collaborative", "guided", "autonomous"},
}
EXPANSION = {
    "minimal": {"modes.workflow": "minimal", "docs.density": "terse", "qa.level": "minimal",
                "modes.story_granularity": "coarse", "modes.review_mode": "solo",
                "team.size": "individual"},
    "standard": {"modes.workflow": "standard", "docs.density": "balanced", "qa.level": "standard",
                 "modes.story_granularity": "balanced", "modes.review_mode": "lean",
                 "team.size": "individual"},
    "full": {"modes.workflow": "full", "docs.density": "thorough", "qa.level": "full",
             "modes.story_granularity": "fine", "modes.review_mode": "full",
             "team.size": "studio"},
}
ALWAYS_ASK = {"scope_changes", "file_deletions", "schema_changes"}


def _valid(key: str, value: object) -> bool:
    allowed = ENUMS.get(key)
    return isinstance(value, str) and (allowed is None or value in allowed)


def resolve(project: dict, local: dict | None = None, legacy: dict | None = None) -> dict:
    """Return {key: (value, source)} using the upstream precedence order."""
    local, legacy = local or {}, legacy or {}
    out, notes = {}, []
    keys = set(DEFAULTS) | set(ENUMS)
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
            rigor = project.get("modes.rigor", DEFAULTS["modes.rigor"])
            if not _valid("modes.rigor", rigor):
                notes.append(f"modes.rigor: '{rigor}' invalid; ignored")
                rigor = DEFAULTS["modes.rigor"]
            if key in EXPANSION.get(rigor, {}):
                out[key] = (EXPANSION[rigor][key], f"rigor:{rigor}")
            elif key in DEFAULTS:
                out[key] = (DEFAULTS[key], "default")
            else:
                out[key] = ("", "unset")
    out["_notes"] = notes
    return out


def resolve_code_root(engine: str | None, dirs: set[str]) -> tuple[str | None, str]:
    """Engine first, then an UNAMBIGUOUS directory, else unresolved."""
    by_engine = {"godot": "src", "unity": "Assets", "unreal": "Source"}
    if engine in by_engine:
        return by_engine[engine], "engine.name"
    candidates = [d for d in ("src", "Assets", "Source") if d in dirs]
    if len(candidates) == 1:
        return candidates[0], "detected"
    return None, "unresolved"


STORY_STATES = {
    "Ready": {"In Progress"},
    "Blocked": {"In Progress"},
    "In Progress": {"Complete"},
    "Complete": set(),
}


@dataclass
class Story:
    name: str
    status: str = "Ready"
    answer: str | None = None  # the user's reply to "may I start?"

    def start(self) -> str:
        if self.status not in ("Ready", "Blocked"):
            return f"refused: {self.status} cannot start"
        if self.answer not in ("yes", "approved"):
            # A skipped/dismissed question is NOT a yes.
            return "waiting: no explicit approval"
        self.status = "In Progress"
        return "started"

    def close(self, verdict: str) -> str:
        if verdict != "PASS" or self.status != "In Progress":
            return f"refused: verdict={verdict} status={self.status}"
        self.status = "Complete"
        return "closed"


PASS, NOTES, UNKNOWN, FAIL = "PASS", "PASS_WITH_NOTES", "UNKNOWN", "FAIL"
RANK = {FAIL: 3, UNKNOWN: 2, NOTES: 1, PASS: 0}


def verdict(criteria: list[tuple[str, str]]) -> str:
    """criteria: (name, state) where state is COVERED, DEFERRED, UNTESTED, or FAILS."""
    states = {state for _, state in criteria}
    if "FAILS" in states:
        return FAIL
    if "UNTESTED" in states:
        return UNKNOWN
    if "DEFERRED" in states:
        return NOTES
    return PASS


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def receipt(paths: list[Path]) -> dict[str, str]:
    return {str(p): digest(p) for p in paths if p.is_file()}


def evidence_state(stamp: dict[str, str] | None, paths: list[Path]) -> list[str]:
    """UNCHANGED / CHANGED / NEW / GONE / RECEIPT_NONE, never a silent pass."""
    if not stamp:
        return ["RECEIPT_NONE"] + [f"NEW: {p}" for p in paths]
    rows = []
    for p in paths:
        if not p.exists():
            rows.append(f"GONE: {p}")
        elif str(p) not in stamp:
            rows.append(f"NEW: {p}")
        elif digest(p) == stamp[str(p)]:
            rows.append(f"UNCHANGED: {p}")
        else:
            rows.append(f"CHANGED: {p}")
    for old in set(stamp) - {str(p) for p in paths}:
        if not Path(old).exists():
            rows.append(f"GONE: {old}")
    return rows


def next_id(kind: str, seen: list[str]) -> str:
    """Highest + 1; a deleted id is never handed out again."""
    nums = [int(x.rsplit("-", 1)[-1]) for x in seen if x.rsplit("-", 1)[-1].isdigit()]
    return f"{kind}-{max(nums, default=0) + 1:03d}"


def needs_ask(mode: str, category: str) -> bool:
    return mode != "autonomous" or category in ALWAYS_ASK


def demo() -> None:
    project = {"modes.rigor": "standard"}
    cfg = resolve(project, local={"modes.review_mode": "solo"})
    print("config:", {k: v for k, v in cfg.items() if not k.startswith("_")})
    print("invalid enum:", resolve({"modes.rigor": "strict"})["modes.workflow"])
    print("code root:", resolve_code_root("unity", {"src", "Assets"}))
    print("code root ambiguous:", resolve_code_root(None, {"src", "Assets"}))

    s = Story("parry")
    print("start without answer:", s.start())
    s.answer = "yes"
    print("start with answer:", s.start())
    print("close on UNKNOWN:", s.close(UNKNOWN))
    print("close on PASS:", s.close(PASS))

    print("verdict mixed:", verdict([("ac1", "COVERED"), ("ac2", "DEFERRED")]))
    print("verdict untested:", verdict([("ac1", "COVERED"), ("ac2", "UNTESTED")]))

    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "combat.gd"
        f.write_text("var parry := true\n", encoding="utf-8")
        stamp = receipt([f])
        print("evidence fresh:", evidence_state(stamp, [f]))
        f.write_text("var parry := true\nvar iframes := 8\n", encoding="utf-8")
        print("evidence stale:", evidence_state(stamp, [f]))
    print("ids:", next_id("story", ["story-001", "story-007", "story-003"]))

if __name__ == "__main__":
    demo()
