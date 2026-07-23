from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EMOTIONAL = ROOT / "main/stackchan/modifiers/emotional_expression.h"
SPEAKING = ROOT / "main/stackchan/modifiers/speaking.h"


class ExpressiveMotionBoundsTests(unittest.TestCase):
    def test_idle_motion_is_anchored_to_startup_pose_and_servo_limits(self) -> None:
        source = EMOTIONAL.read_text(encoding="utf-8")
        self.assertIn("_home_angles = motion.getCurrentAngles();", source)
        self.assertIn("motion.pitchServo().getAngleLimit()", source)
        self.assertIn("safe_pitch_min", source)
        self.assertIn("safe_pitch_max", source)
        self.assertNotIn("motion.moveWithSpeed(yaw_delta, pitch_delta, 120);", source)

    def test_speaking_motion_never_commands_below_its_starting_pitch(self) -> None:
        source = SPEAKING.read_text(encoding="utf-8")
        self.assertIn("safe_pitch_min =", source)
        self.assertIn("safe_pitch_max =", source)
        self.assertIn("target_pitch = uitk::clamp(target_pitch, safe_pitch_min, safe_pitch_max);", source)


if __name__ == "__main__":
    unittest.main()
