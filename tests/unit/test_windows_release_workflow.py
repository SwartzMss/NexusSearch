"""Tests for the versioned Windows portable release contract."""

# SPDX-License-Identifier: AGPL-3.0-or-later

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def load_workflow(relative_path: str) -> dict:
    return yaml.safe_load(read_text(relative_path))


class WindowsReleaseWorkflowTestCase(unittest.TestCase):
    """Keep development and release workflows on the same package contract."""

    def test_shared_packager(self):
        workflow = read_text(".github/workflows/windows-portable.yml")
        self.assertIn("pwsh packaging/build_portable.ps1", workflow)
        self.assertNotIn("Compress-Archive", workflow)
        self.assertNotIn("smoke_test.py $executable", workflow)
        self.assertNotIn("gh release create", workflow)
        self.assertNotIn("contents: write", workflow)

    def test_tag_release_contract(self):
        workflow = load_workflow(".github/workflows/windows-release.yml")
        self.assertEqual(workflow["on"], {"push": {"tags": ["v*"]}})
        self.assertEqual(workflow["permissions"], {"contents": "write"})
        release_job = workflow["jobs"]["build-and-release"]
        steps = "\n".join(step.get("run", "") for step in release_job["steps"])
        self.assertIn("packaging/nexussearch.spec", steps)
        self.assertIn("packaging/build_portable.ps1", steps)
        self.assertIn("NexusSearch-Windows-x64.zip", steps)
        self.assertIn("SHA256SUMS.txt", steps)
        self.assertIn("gh release create", steps)

    def test_packager_runtime_checks(self):
        script = read_text("packaging/build_portable.ps1")
        for required_text in (
            "prepare_portable.py",
            "smoke_test.py",
            "--health-only",
            "settings-smoke.yml",
            "NexusSearch-Windows-x64.zip",
            "_internal/searx/engines/google.py",
            "LICENSE",
            "AUTHORS.rst",
            "_internal/LICENSE",
            "_internal/AUTHORS.rst",
        ):
            self.assertIn(required_text, script)

    def test_build_freezes_version_metadata_before_pyinstaller(self):
        """Both Windows builds freeze version metadata before analysis."""
        for relative_path in (
            ".github/workflows/windows-portable.yml",
            ".github/workflows/windows-release.yml",
        ):
            workflow = load_workflow(relative_path)
            job_name = "build-and-smoke" if "build-and-smoke" in workflow["jobs"] else "build-and-release"
            steps = workflow["jobs"][job_name]["steps"]
            run_steps = [step.get("run", "") for step in steps]
            freeze_index = next(i for i, run in enumerate(run_steps) if "python -m searx.version freeze" in run)
            build_index = next(i for i, run in enumerate(run_steps) if "packaging/nexussearch.spec" in run)
            self.assertLess(freeze_index, build_index, relative_path)

    def test_spec_bundles_frozen_version_module(self):
        """PyInstaller includes the dynamically imported frozen module."""
        spec = read_text("packaging/nexussearch.spec")
        self.assertIn("version_frozen.py", spec)
        self.assertIn("searx.version_frozen", spec)


if __name__ == "__main__":
    unittest.main()
