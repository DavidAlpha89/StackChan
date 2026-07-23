import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "render_local_ota_config.py"


class RenderLocalOtaConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("render_local_ota_config", SCRIPT)
        assert spec is not None and spec.loader is not None
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_rejects_missing_or_unsafe_token(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "sdkconfig.local.defaults"
            for token in ("", "short", "x" * 31, "x" * 32 + '"'):
                with self.subTest(token_length=len(token)):
                    with self.assertRaises(self.module.ConfigRenderError):
                        self.module.render(
                            {"STACKCHAN_BOOTSTRAP_TOKEN": token}, output
                        )
                    self.assertFalse(output.exists())

    def test_writes_private_local_defaults_without_logging_token(self):
        token = "A" * 43
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "sdkconfig.local.defaults"
            result = self.module.render(
                {"STACKCHAN_BOOTSTRAP_TOKEN": token}, output
            )

            self.assertEqual(result, output)
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            self.assertEqual(
                output.read_text(encoding="utf-8").splitlines(),
                [
                    "CONFIG_FORCE_CONFIG_OTA_URL=y",
                    "CONFIG_FORCE_AI_AGENT_ON_BOOT=y",
                    f'CONFIG_OTA_URL="http://192.168.50.200:9462/ota/{token}"',
                ],
            )


if __name__ == "__main__":
    unittest.main()
