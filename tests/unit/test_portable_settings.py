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


if __name__ == "__main__":
    unittest.main()
