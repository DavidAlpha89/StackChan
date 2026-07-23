from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


FIRMWARE_ROOT = Path(__file__).resolve().parents[1]
RENDERER_PATH = FIRMWARE_ROOT / "tools" / "render_local_ota_config.py"


spec = importlib.util.spec_from_file_location("render_local_ota_config", RENDERER_PATH)
assert spec and spec.loader
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class ForceAiAgentOnBootTests(unittest.TestCase):
    def test_renderer_targets_the_overlay_filename_used_by_cmake(self) -> None:
        self.assertEqual(renderer.DEFAULT_OUTPUT.name, "sdkconfig.defaults.local")

    def test_renderer_enables_forced_ai_agent_startup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "sdkconfig.defaults.local"
            renderer.render({"STACKCHAN_BOOTSTRAP_TOKEN": "A" * 43}, output)
            content = output.read_text(encoding="utf-8")

        self.assertIn("CONFIG_FORCE_AI_AGENT_ON_BOOT=y\n", content)

    def test_project_defines_and_uses_forced_ai_agent_startup(self) -> None:
        kconfig = (FIRMWARE_ROOT / "main" / "Kconfig.projbuild").read_text(
            encoding="utf-8"
        )
        main_cpp = (FIRMWARE_ROOT / "main" / "main.cpp").read_text(encoding="utf-8")

        self.assertIn("config FORCE_AI_AGENT_ON_BOOT", kconfig)
        self.assertIn("CONFIG_FORCE_AI_AGENT_ON_BOOT", main_cpp)
        self.assertIn("const bool skip_mooncake = true", main_cpp)


if __name__ == "__main__":
    unittest.main()
