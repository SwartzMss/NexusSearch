"""Tests for release and deterministic smoke configurations."""

# SPDX-License-Identifier: AGPL-3.0-or-later

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]


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

    def test_release_config_disables_tracker_url_remover(self):
        """The portable config skips the external tracker-rule fetch."""
        settings = yaml.safe_load((ROOT / "packaging/settings.yml").read_text(encoding="utf-8"))
        plugin = settings["plugins"]["searx.plugins.tracker_url_remover.SXNGPlugin"]
        self.assertFalse(plugin["active"])

    def test_upstream_config_keeps_tracker_url_remover_enabled(self):
        """The upstream SearXNG default remains unchanged."""
        settings = yaml.safe_load((ROOT / "searx/settings.yml").read_text(encoding="utf-8"))
        plugin = settings["plugins"]["searx.plugins.tracker_url_remover.SXNGPlugin"]
        self.assertTrue(plugin["active"])


if __name__ == "__main__":
    unittest.main()
