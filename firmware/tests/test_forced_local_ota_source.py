import unittest
from pathlib import Path


FIRMWARE = Path(__file__).resolve().parents[1]
KCONFIG = FIRMWARE / "xiaozhi-esp32" / "main" / "Kconfig.projbuild"
OTA_SOURCE = FIRMWARE / "xiaozhi-esp32" / "main" / "ota.cc"


class ForcedLocalOtaSourceTests(unittest.TestCase):
    def test_kconfig_exposes_explicit_force_switch(self):
        source = KCONFIG.read_text(encoding="utf-8")

        self.assertIn("config FORCE_CONFIG_OTA_URL", source)
        self.assertIn('bool "Always use the configured OTA URL"', source)
        self.assertIn("default n", source)

    def test_ota_source_uses_config_url_only_when_force_switch_is_enabled(self):
        source = OTA_SOURCE.read_text(encoding="utf-8")

        expected = """std::string Ota::GetCheckVersionUrl() {
#ifdef CONFIG_FORCE_CONFIG_OTA_URL
    return CONFIG_OTA_URL;
#else
    Settings settings(\"wifi\", false);
    std::string url = settings.GetString(\"ota_url\");
    if (url.empty()) {
        url = CONFIG_OTA_URL;
    }
    return url;
#endif
}"""
        self.assertIn(expected, source)


if __name__ == "__main__":
    unittest.main()
