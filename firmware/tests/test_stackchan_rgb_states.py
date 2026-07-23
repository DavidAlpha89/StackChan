from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DISPLAY = ROOT / "main/hal/board/stackchan_display.cc"


class StackChanRgbStateTests(unittest.TestCase):
    def test_listening_and_speaking_use_full_rgb_ring(self) -> None:
        source = DISPLAY.read_text(encoding="utf-8")
        listening = source.split(
            "strcmp(status, Lang::Strings::LISTENING) == 0", 1
        )[1].split("Lang::Strings::STANDBY", 1)[0]
        speaking = source.split(
            "strcmp(status, Lang::Strings::SPEAKING) == 0", 1
        )[1].split("} else {", 1)[0]

        self.assertIn("GetHAL().showRgbColor(0, 50, 0);", listening)
        self.assertIn("GetHAL().showRgbColor(0, 0, 50);", speaking)

    def test_standby_clears_full_rgb_ring(self) -> None:
        source = DISPLAY.read_text(encoding="utf-8")
        standby = source.split(
            "strcmp(status, Lang::Strings::STANDBY) == 0", 1
        )[1].split("Lang::Strings::SPEAKING", 1)[0]

        self.assertIn("GetHAL().showRgbColor(0, 0, 0);", standby)

    def test_thinking_uses_blue_without_starting_speaking_modifier(self) -> None:
        source = DISPLAY.read_text(encoding="utf-8")
        thinking = source.split('strcmp(status, "Thinking...") == 0', 1)[1].split(
            "Lang::Strings::SPEAKING", 1
        )[0]

        self.assertIn("GetHAL().showRgbColor(0, 0, 50);", thinking)
        self.assertNotIn("SpeakingModifier", thinking)


if __name__ == "__main__":
    unittest.main()