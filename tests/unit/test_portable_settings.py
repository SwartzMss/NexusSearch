"""Tests for release and deterministic smoke configurations."""

# SPDX-License-Identifier: AGPL-3.0-or-later

import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import yaml


ROOT = Path(__file__).parents[2]
TRACKER_PLUGIN = "searx.plugins.tracker_url_remover.SXNGPlugin"
PORTABLE_SETTINGS = ("packaging/settings.yml", "packaging/settings-smoke.yml")


class PortableSettingsTestCase(unittest.TestCase):
    """Keep the user-facing and CI-only engine policies separate."""

    def test_release_config(self):
        """The release config must not restrict the engine list."""
        settings = yaml.safe_load((ROOT / "packaging/settings.yml").read_text(encoding="utf-8"))
        self.assertTrue(settings["use_default_settings"])
        self.assertNotIn("engines", settings)

    def test_smoke_config(self):
        """The smoke config explicitly limits engines for deterministic CI."""
        settings = yaml.safe_load((ROOT / "packaging/settings-smoke.yml").read_text(encoding="utf-8"))
        self.assertEqual(settings["use_default_settings"]["engines"]["keep_only"], ["nexussearch demo"])
        self.assertEqual(settings["engines"][0]["engine"], "nexussearch_demo")

    def test_portable_configs_exclude_tracker_and_preserve_plugins(self):
        """Portable configs omit only the plugin that fetches tracker rules."""
        upstream = yaml.safe_load((ROOT / "searx/settings.yml").read_text(encoding="utf-8"))
        expected_plugins = set(upstream["plugins"]) - {TRACKER_PLUGIN}
        for relative_path in PORTABLE_SETTINGS:
            settings = yaml.safe_load((ROOT / relative_path).read_text(encoding="utf-8"))
            self.assertEqual(set(settings["plugins"]), expected_plugins, relative_path)

    def test_portable_configs_do_not_initialize_tracker_patterns(self):
        """Loading either portable plugin set never initializes tracker rules."""
        from searx import data
        from searx.plugins import PluginStorage

        for relative_path in PORTABLE_SETTINGS:
            settings = yaml.safe_load((ROOT / relative_path).read_text(encoding="utf-8"))
            storage = PluginStorage()
            with patch.object(data.TRACKER_PATTERNS, "init") as tracker_init:
                storage.load_settings(settings["plugins"])
                storage.init(Mock())
                tracker_init.assert_not_called()

    def test_upstream_config_keeps_tracker_url_remover_enabled(self):
        """The upstream SearXNG default remains unchanged."""
        settings = yaml.safe_load((ROOT / "searx/settings.yml").read_text(encoding="utf-8"))
        plugin = settings["plugins"]["searx.plugins.tracker_url_remover.SXNGPlugin"]
        self.assertTrue(plugin["active"])


if __name__ == "__main__":
    unittest.main()
