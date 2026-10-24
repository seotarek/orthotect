import unittest
import os
import sys
import json
import tempfile
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.config import (
    load_orthotect_config,
    find_config_file,
    is_path_excluded,
    get_cwv_config,
    get_bidi_config,
    get_contrast_config,
    DEFAULT_CONFIG
)

class TestOrthotectConfig(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_config_fallback(self):
        """When no config file exists, return default config."""
        cfg, cfg_file = load_orthotect_config(self.temp_dir.name)
        self.assertIsNone(cfg_file)
        self.assertEqual(cfg["cwv"]["maxDomDepth"], 32)
        self.assertFalse(cfg["bidi"]["allowCamelCase"])
        self.assertIn("**/node_modules/**", cfg["exclude"])

    def test_custom_config_override_and_deep_merge(self):
        """Custom configuration must override specific keys while preserving other defaults."""
        custom_data = {
            "exclude": ["custom_build/**", "legacy/**"],
            "cwv": {
                "maxDomDepth": 48
            }
        }
        cfg_path = os.path.join(self.temp_dir.name, "orthotect.config.json")
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(custom_data, f)

        cfg, found_file = load_orthotect_config(self.temp_dir.name)
        self.assertEqual(found_file, cfg_path)
        self.assertEqual(cfg["cwv"]["maxDomDepth"], 48)
        # cwv.maxDomNodes should be preserved from default
        self.assertEqual(cfg["cwv"]["maxDomNodes"], 1500)
        # bidi.allowCamelCase should be preserved from default
        self.assertFalse(cfg["bidi"]["allowCamelCase"])
        # exclude should have custom entries
        self.assertEqual(cfg["exclude"], ["custom_build/**", "legacy/**"])

    def test_upward_search_finds_config_in_parent(self):
        """find_config_file must traverse upward from deep child directories."""
        cfg_path = os.path.join(self.temp_dir.name, "orthotect.config.json")
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump({"cwv": {"maxDomDepth": 20}}, f)

        sub_sub_dir = os.path.join(self.temp_dir.name, "src", "components", "buttons")
        os.makedirs(sub_sub_dir, exist_ok=True)

        found = find_config_file(sub_sub_dir)
        self.assertEqual(found, cfg_path)

        cfg, _ = load_orthotect_config(sub_sub_dir)
        self.assertEqual(cfg["cwv"]["maxDomDepth"], 20)

    def test_is_path_excluded(self):
        """Evaluates whether paths correctly match glob exclusion patterns."""
        config = {
            "exclude": [
                "**/node_modules/**",
                "dist/**",
                "*.min.js",
                "legacy-folder/**"
            ]
        }
        self.assertTrue(is_path_excluded("node_modules/pkg/index.js", config))
        self.assertTrue(is_path_excluded("/root/project/node_modules/pkg/index.js", config))
        self.assertTrue(is_path_excluded("dist/bundle.js", config))
        self.assertTrue(is_path_excluded("src/app.min.js", config))
        self.assertTrue(is_path_excluded("legacy-folder/old.css", config))

        # Non-matching paths
        self.assertFalse(is_path_excluded("src/components/Card.tsx", config))
        self.assertFalse(is_path_excluded("docs/index.html", config))

    def test_corrupted_config_graceful_recovery(self):
        """Invalid JSON in config file should output warning and cleanly return default config."""
        cfg_path = os.path.join(self.temp_dir.name, "orthotect.config.json")
        with open(cfg_path, "w", encoding="utf-8") as f:
            f.write("INVALID JSON CONTENT { [")

        cfg, found_file = load_orthotect_config(self.temp_dir.name)
        self.assertIsNone(found_file)
        self.assertEqual(cfg["cwv"]["maxDomDepth"], 32)

    def test_helper_getters(self):
        """Helper getters must extract subsections with fallback defaults."""
        config = {"cwv": {"maxDomDepth": 40}, "bidi": {"allowCamelCase": True}}
        self.assertEqual(get_cwv_config(config)["maxDomDepth"], 40)
        self.assertTrue(get_bidi_config(config)["allowCamelCase"])
        self.assertEqual(get_contrast_config(config)["level"], "AA")

if __name__ == '__main__':
    unittest.main()
