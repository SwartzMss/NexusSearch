# SPDX-License-Identifier: AGPL-3.0-or-later

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


_SMOKE_SPEC = importlib.util.spec_from_file_location(
    "nexussearch_smoke", Path(__file__).parents[2] / "packaging" / "smoke_test.py"
)
assert _SMOKE_SPEC and _SMOKE_SPEC.loader
smoke = importlib.util.module_from_spec(_SMOKE_SPEC)
_SMOKE_SPEC.loader.exec_module(smoke)


class FakeProcess:
    def __init__(self, returncode=None):
        self.returncode = returncode

    def poll(self):
        return self.returncode

    def terminate(self):
        self.returncode = 1

    def wait(self, timeout=None):
        return self.returncode


class SmokeTestCase(unittest.TestCase):
    def test_success_ignores_test_owned_termination_exit_code(self):
        process = FakeProcess()
        responses = [
            (200, "application/json", b'{"status":"ok"}'),
            (200, "application/json", b'{"results":[{"title":"t","url":"u","content":"c"}]}'),
        ]
        with (
            patch.object(smoke.subprocess, "Popen", return_value=process),
            patch.object(smoke, "get", side_effect=responses),
            patch.object(sys, "argv", ["smoke_test.py", "nexussearch.exe"]),
        ):
            self.assertEqual(smoke.main(), 0)

    def test_early_exit_includes_process_diagnostics(self):
        process = FakeProcess(returncode=7)
        with (
            patch.object(smoke.subprocess, "Popen", return_value=process),
            patch.object(smoke, "get", side_effect=AssertionError("health must not be called")),
            patch.object(sys, "argv", ["smoke_test.py", "nexussearch.exe"]),
        ):
            with self.assertRaisesRegex(RuntimeError, "exit code: 7") as raised:
                smoke.main()
        self.assertIn("stdout:", str(raised.exception))
        self.assertIn("stderr:", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
