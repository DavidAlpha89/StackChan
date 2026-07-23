from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
APPLICATION = ROOT / "xiaozhi-esp32/main/application.cc"
HEADER = ROOT / "xiaozhi-esp32/main/application.h"


class ListeningAudioStartupTests(unittest.TestCase):
    def test_listening_transition_directly_ensures_audio_startup(self) -> None:
        source = APPLICATION.read_text(encoding="utf-8")
        setter = source.split("void Application::SetListeningMode(ListeningMode mode) {", 1)[1].split(
            "}", 1
        )[0]
        self.assertIn("SetDeviceState(kDeviceStateListening);", setter)
        self.assertIn("EnsureListeningAudioStarted();", setter)

    def test_startup_helper_is_idempotent_and_sends_listen_start(self) -> None:
        source = APPLICATION.read_text(encoding="utf-8")
        helper = source.split("void Application::EnsureListeningAudioStarted() {", 1)[1].split(
            "void Application::", 1
        )[0]
        self.assertIn("audio_service_.IsAudioProcessorRunning()", helper)
        self.assertIn("protocol_->SendStartListening(listening_mode_);", helper)
        self.assertIn("audio_service_.EnableVoiceProcessing(true);", helper)

    def test_popup_finishes_before_microphone_processing_begins(self) -> None:
        source = APPLICATION.read_text(encoding="utf-8")
        helper = source.split("void Application::EnsureListeningAudioStarted() {", 1)[1].split(
            "void Application::", 1
        )[0]
        popup = helper.index("audio_service_.PlaySound(Lang::Sounds::OGG_POPUP);")
        wait = helper.index("audio_service_.WaitForPlaybackQueueEmpty();", popup)
        microphone = helper.index("audio_service_.EnableVoiceProcessing(true);")
        self.assertLess(popup, wait)
        self.assertLess(wait, microphone)

    def test_helper_is_declared(self) -> None:
        header = HEADER.read_text(encoding="utf-8")
        self.assertIn("void EnsureListeningAudioStarted();", header)


if __name__ == "__main__":
    unittest.main()
