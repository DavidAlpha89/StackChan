from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
APPLICATION = ROOT / "xiaozhi-esp32/main/application.cc"


class StackChanThinkingProtocolTests(unittest.TestCase):
    def test_thinking_message_updates_display_without_entering_speaking_state(self) -> None:
        source = APPLICATION.read_text(encoding="utf-8")
        thinking = source.split('strcmp(type->valuestring, "thinking") == 0', 1)[1].split(
            'strcmp(type->valuestring, "tts") == 0', 1
        )[0]

        self.assertIn('display->SetStatus("Thinking...");', thinking)
        self.assertNotIn("SetDeviceState(kDeviceStateSpeaking)", thinking)


if __name__ == "__main__":
    unittest.main()