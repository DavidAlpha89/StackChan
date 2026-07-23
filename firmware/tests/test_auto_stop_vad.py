from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
APPLICATION = ROOT / "xiaozhi-esp32/main/application.cc"
PROCESSOR = ROOT / "xiaozhi-esp32/main/audio/processors/afe_audio_processor.cc"


class AutoStopVadTests(unittest.TestCase):
    def test_auto_stop_listening_uses_authoritative_vad_callback_value(self) -> None:
        source = APPLICATION.read_text(encoding="utf-8")
        callback = source.split("callbacks.on_vad_change = [this](bool speaking) {", 1)[1].split(
            "};", 1
        )[0]

        self.assertIn("!speaking", callback)
        self.assertIn("listening_mode_ == kListeningModeAutoStop", callback)
        self.assertIn("StopListening();", callback)

    def test_conversation_vad_rejects_persistent_ambient_noise(self) -> None:
        source = PROCESSOR.read_text(encoding="utf-8")
        self.assertIn("afe_config->vad_mode = VAD_MODE_3;", source)

    def test_vad_transitions_are_logged_for_physical_diagnostics(self) -> None:
        source = PROCESSOR.read_text(encoding="utf-8")
        self.assertIn('ESP_LOGI(TAG, "VAD: speech")', source)
        self.assertIn('ESP_LOGI(TAG, "VAD: silence")', source)


if __name__ == "__main__":
    unittest.main()
