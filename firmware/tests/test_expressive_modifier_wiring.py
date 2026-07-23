from pathlib import Path
import unittest


DISPLAY_SOURCE = (
    Path(__file__).resolve().parents[1]
    / "main"
    / "hal"
    / "board"
    / "stackchan_display.cc"
)


class ExpressiveModifierWiringTests(unittest.TestCase):
    def test_idle_state_does_not_run_competing_head_motion_modifiers(self) -> None:
        source = DISPLAY_SOURCE.read_text(encoding="utf-8")
        start = source.index("if (is_idle) {")
        end = source.index("_is_xiaozhi_idle = true;", start)
        idle_state = source[start:end]

        self.assertIn("EmotionalExpressionModifier", idle_state)
        self.assertIn("if (emotional_expression_modifier_id_ < 0)", idle_state)
        self.assertNotIn("CreateIdleMotionModifier();", idle_state)

    def test_non_idle_state_removes_each_modifier_independently(self) -> None:
        source = DISPLAY_SOURCE.read_text(encoding="utf-8")
        start = source.index("if (is_idle) {")
        end = source.index("_is_xiaozhi_idle = false;", start)
        status_transition = source[start:end]
        expected = """if (idle_motion_modifier_id_ >= 0) {
            stackchan.removeModifier(idle_motion_modifier_id_);
            idle_motion_modifier_id_ = -1;
        }
        if (idle_expression_modifier_id_ >= 0) {
            stackchan.removeModifier(idle_expression_modifier_id_);
            idle_expression_modifier_id_ = -1;
        }
        if (emotional_expression_modifier_id_ >= 0) {
            stackchan.removeModifier(emotional_expression_modifier_id_);
            emotional_expression_modifier_id_ = -1;
        }"""
        self.assertIn(expected, status_transition)


if __name__ == "__main__":
    unittest.main()
