# SPDX-License-Identifier: AGPL-3.0-or-later

import unittest
from unittest.mock import patch

from searx import valkeydb


class ValkeyDbPlatformTestCase(unittest.TestCase):
    def test_current_user_name_has_windows_safe_fallback(self):
        with patch.object(valkeydb, "pwd", None), patch.object(
            valkeydb.getpass, "getuser", return_value="portable"
        ):
            self.assertEqual(valkeydb.current_user_name(), "portable")
