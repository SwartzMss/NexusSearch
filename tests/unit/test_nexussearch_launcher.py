"""Tests for the portable NexusSearch launcher."""

# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import nexussearch_launcher


class LauncherTestCase(unittest.TestCase):
    """Verify launcher path and environment setup."""

    def test_adjacent_config(self):
        """Use a settings file next to the launcher source."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "launcher.py"
            settings = Path(temporary_directory) / "settings.yml"
            source.touch()
            settings.touch()
            with (
                patch.object(nexussearch_launcher, "__file__", str(source)),
                patch.dict(os.environ, {}, clear=True),
            ):
                self.assertEqual(nexussearch_launcher.configure_environment(), settings)
                self.assertEqual(os.environ["SEARXNG_SETTINGS_PATH"], str(settings))
                self.assertEqual(os.environ["SEARXNG_DISABLE_ETC_SETTINGS"], "true")

    def test_frozen_runtime_dir(self):
        """Use the executable directory for a frozen application."""
        with (
            patch.object(sys, "frozen", True, create=True),
            patch.object(sys, "executable", "/tmp/NexusSearch/nexussearch.exe"),
        ):
            self.assertEqual(nexussearch_launcher.runtime_directory(), Path("/tmp/NexusSearch"))

    def test_internal_config_fallback(self):
        """Use PyInstaller's internal settings when no root copy exists."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            source = base / "launcher.py"
            settings = base / "_internal" / "settings.yml"
            source.touch()
            settings.parent.mkdir()
            settings.touch()
            with (
                patch.object(nexussearch_launcher, "__file__", str(source)),
                patch.dict(os.environ, {}, clear=True),
            ):
                self.assertEqual(nexussearch_launcher.configure_environment(), settings)
                self.assertEqual(os.environ["SEARXNG_SETTINGS_PATH"], str(settings))

    def test_explicit_config_wins(self):
        """Preserve an explicitly selected smoke configuration."""
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            source = base / "launcher.py"
            explicit = base / "settings-smoke.yml"
            adjacent = base / "settings.yml"
            source.touch()
            explicit.touch()
            adjacent.touch()
            with (
                patch.object(nexussearch_launcher, "__file__", str(source)),
                patch.dict(os.environ, {"SEARXNG_SETTINGS_PATH": str(explicit)}, clear=True),
            ):
                self.assertEqual(nexussearch_launcher.configure_environment(), explicit)
                self.assertEqual(os.environ["SEARXNG_SETTINGS_PATH"], str(explicit))
                self.assertEqual(os.environ["SEARXNG_DISABLE_ETC_SETTINGS"], "true")


if __name__ == "__main__":
    unittest.main()
