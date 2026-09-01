"""Tests for the portable runtime smoke-test contract."""

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
    """Minimal process double for smoke lifecycle tests."""

    def __init__(self, returncode=None):
        self.returncode = returncode

    def poll(self):
        return self.returncode

    def terminate(self):
        self.returncode = 1

    def wait(self, timeout=None):
        del timeout
        return self.returncode


class SmokeTestCase(unittest.TestCase):
    """Verify success and failure handling for the child process."""

    def test_shutdown_code_ignored(self):
        """A test-owned terminate with a nonzero code still means success."""
        process = FakeProcess()
        responses = [
            (200, "application/json", b'{"status":"ok"}'),
            (
                200,
                "application/json",
                b'{"results":[{"title":"t","url":"u","content":"c","engine":"demo"}]}',
            ),
        ]
        with (
            patch.object(smoke.subprocess, "Popen", return_value=process),
            patch.object(smoke, "get", side_effect=responses),
            patch.object(sys, "argv", ["smoke_test.py", "nexussearch.exe"]),
        ):
            self.assertEqual(smoke.main(), 0)

    def test_health_only_skips_search(self):
        """Health-only mode validates startup without querying search."""
        process = FakeProcess()
        with (
            patch.object(smoke.subprocess, "Popen", return_value=process),
            patch.object(smoke, "get", return_value=(200, "application/json", b'{"status":"ok"}')),
            patch.object(sys, "argv", ["smoke_test.py", "nexussearch.exe", "--health-only"]),
        ):
            self.assertEqual(smoke.main(), 0)

    def test_early_exit_diagnostics(self):
        """An early child exit includes its status and captured output."""
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

    def test_empty_results_rejected(self):
        """An empty result list does not prove that search works."""
        with self.assertRaisesRegex(RuntimeError, "contains no results"):
            smoke.validate_search_response({"results": []})

    def test_engine_metadata_required(self):
        """A result must identify the engine that produced it."""
        result = {"results": [{"title": "t", "url": "u", "content": "c"}]}
        with self.assertRaisesRegex(RuntimeError, "engine metadata"):
            smoke.validate_search_response(result)


if __name__ == "__main__":
    unittest.main()
