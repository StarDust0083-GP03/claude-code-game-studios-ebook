import unittest
from pathlib import Path
import tempfile

from mini_studio import (
    PASS, NOTES, UNKNOWN, FAIL, Story, evidence_state, needs_ask, next_id,
    receipt, resolve, resolve_code_root, verdict,
)


class ConfigTest(unittest.TestCase):
    def test_local_wins_for_whitelisted_key(self):
        cfg = resolve({"modes.rigor": "standard"}, {"modes.review_mode": "solo"})
        self.assertEqual(cfg["modes.review_mode"], ("solo", "project.local.yaml"))

    def test_local_ignored_for_protected_key(self):
        cfg = resolve({"qa.level": "full"}, {"qa.level": "minimal"})
        self.assertEqual(cfg["qa.level"], ("full", "project.yaml"))

    def test_explicit_key_beats_rigor_expansion(self):
        cfg = resolve({"modes.rigor": "full", "modes.workflow": "minimal"})
        self.assertEqual(cfg["modes.workflow"], ("minimal", "project.yaml"))

    def test_invalid_enum_falls_through(self):
        cfg = resolve({"modes.rigor": "strict"})
        self.assertEqual(cfg["modes.workflow"][0], "minimal")
        self.assertTrue(any("not a valid enum" in n for n in cfg["_notes"]))


class CodeRootTest(unittest.TestCase):
    def test_engine_wins(self):
        self.assertEqual(resolve_code_root("unity", {"src"}), ("Assets", "engine.name"))

    def test_single_dir_detected(self):
        self.assertEqual(resolve_code_root(None, {"src", "design"}), ("src", "detected"))

    def test_ambiguous_is_unresolved(self):
        self.assertEqual(resolve_code_root(None, {"src", "Assets"}), (None, "unresolved"))


class StoryTest(unittest.TestCase):
    def test_skipped_question_is_not_approval(self):
        s = Story("parry")
        self.assertEqual(s.status, "Ready")
        self.assertIn("waiting", s.start())
        self.assertEqual(s.status, "Ready")

    def test_no_close_on_unknown(self):
        s = Story("parry", answer="yes")
        s.start()
        self.assertIn("refused", s.close(UNKNOWN))
        self.assertEqual(s.status, "In Progress")

    def test_close_on_pass(self):
        s = Story("parry", answer="yes")
        s.start()
        self.assertEqual(s.close(PASS), "closed")
        self.assertEqual(s.status, "Complete")


class VerdictTest(unittest.TestCase):
    def test_fail_outranks_unknown(self):
        self.assertEqual(verdict([("a", "UNTESTED"), ("b", "FAILS")]), FAIL)

    def test_unknown_outranks_pass(self):
        self.assertEqual(verdict([("a", "COVERED"), ("b", "UNTESTED")]), UNKNOWN)

    def test_deferred_is_notes(self):
        self.assertEqual(verdict([("a", "COVERED"), ("b", "DEFERRED")]), NOTES)


class EvidenceTest(unittest.TestCase):
    def test_receipt_detects_change_and_gone(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "combat.gd"
            f.write_text("a\n", encoding="utf-8")
            stamp = receipt([f])
            self.assertTrue(evidence_state(stamp, [f])[0].startswith("UNCHANGED"))
            f.write_text("b\n", encoding="utf-8")
            self.assertTrue(evidence_state(stamp, [f])[0].startswith("CHANGED"))
            f.unlink()
            self.assertTrue(evidence_state(stamp, [f])[0].startswith("GONE"))

    def test_missing_receipt_is_loud(self):
        self.assertEqual(evidence_state({}, [Path("nope")])[0], "RECEIPT_NONE")


class RegistryTest(unittest.TestCase):
    def test_ids_are_never_reused(self):
        self.assertEqual(next_id("story", ["story-001", "story-007"]), "story-008")
        self.assertEqual(next_id("story", []), "story-001")


class ModeTest(unittest.TestCase):
    def test_always_ask_survives_autonomous(self):
        self.assertTrue(needs_ask("autonomous", "file_deletions"))
        self.assertFalse(needs_ask("autonomous", "formatting"))


if __name__ == "__main__":
    unittest.main()
