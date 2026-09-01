"""Tests for platform-specific Valkey helpers."""

# SPDX-License-Identifier: AGPL-3.0-or-later

import unittest
from unittest.mock import patch

from searx import valkeydb


class ValkeyDbPlatformTestCase(unittest.TestCase):
    """Verify user-name lookup works without POSIX pwd."""

    def test_windows_user_fallback(self):
        """Use getpass when pwd is unavailable."""
        with (
            patch.object(valkeydb, "pwd", None),
            patch.object(valkeydb.getpass, "getuser", return_value="portable"),
        ):
            self.assertEqual(valkeydb.current_user_name(), "portable")
