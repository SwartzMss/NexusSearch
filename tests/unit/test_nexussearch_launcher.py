# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import nexussearch_launcher


class LauncherTestCase(unittest.TestCase):
    def test_configure_environment_uses_settings_next_to_source(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "launcher.py"
            settings = Path(temporary_directory) / "settings.yml"
            source.touch()
            settings.touch()
            with patch.object(nexussearch_launcher, "__file__", str(source)), patch.dict(
                os.environ, {}, clear=True
            ):
                self.assertEqual(nexussearch_launcher.configure_environment(), settings)
                self.assertEqual(os.environ["SEARXNG_SETTINGS_PATH"], str(settings))
                self.assertEqual(os.environ["SEARXNG_DISABLE_ETC_SETTINGS"], "true")

    def test_runtime_directory_uses_frozen_executable(self):
        with patch.object(sys, "frozen", True, create=True), patch.object(
            sys, "executable", "/tmp/NexusSearch/nexussearch.exe"
        ):
            self.assertEqual(nexussearch_launcher.runtime_directory(), Path("/tmp/NexusSearch"))

    def test_configure_environment_falls_back_to_pyinstaller_internal(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            source = base / "launcher.py"
            settings = base / "_internal" / "settings.yml"
            source.touch()
            settings.parent.mkdir()
            settings.touch()
            with patch.object(nexussearch_launcher, "__file__", str(source)), patch.dict(
                os.environ, {}, clear=True
            ):
                self.assertEqual(nexussearch_launcher.configure_environment(), settings)
                self.assertEqual(os.environ["SEARXNG_SETTINGS_PATH"], str(settings))
