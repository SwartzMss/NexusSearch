# Versioned Windows Portable Releases Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the Windows x64 portable runtime from immutable `v*` tags with stable ZIP and SHA256 release assets while sharing the existing packaging and smoke contract with development CI.

**Architecture:** Move the current Windows workflow's relocation, resource checks, smoke tests, and archive creation into `packaging/build_portable.ps1`. Keep `.github/workflows/windows-portable.yml` as the branch/PR validation workflow and add `.github/workflows/windows-release.yml` as the tag-only publisher that invokes the same build and creates a GitHub Release with `gh`.

**Tech Stack:** GitHub Actions, Windows PowerShell, PyInstaller `onedir`, Python `unittest`, PyYAML, GitHub CLI.

---

### Task 1: Add failing workflow contract tests

**Files:**
- Create: `tests/unit/test_windows_release_workflow.py`

- [ ] **Step 1: Write the failing tests**

Create tests that load both workflow files with `yaml.safe_load` and assert the release contract:

```python
class WindowsReleaseWorkflowTestCase(unittest.TestCase):
    def test_development_workflow_uses_shared_packager(self):
        workflow = read_text(".github/workflows/windows-portable.yml")
        self.assertIn("pwsh packaging/build_portable.ps1", workflow)
        self.assertNotIn("Compress-Archive", workflow)
        self.assertNotIn("smoke_test.py $executable", workflow)

    def test_release_workflow_is_tag_only_and_can_publish(self):
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

    def test_packager_contains_shared_runtime_checks(self):
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
        ):
            self.assertIn(required_text, script)
```

The helper functions should resolve paths from `ROOT = Path(__file__).parents[2]`, read UTF-8 text, and use `yaml.safe_load` for workflow parsing.

- [ ] **Step 2: Run the tests and verify the expected red failure**

Run:

```bash
python -m unittest tests.unit.test_windows_release_workflow -v
```

Expected: FAIL because `packaging/build_portable.ps1` and `.github/workflows/windows-release.yml` do not exist yet.

### Task 2: Extract the shared Windows packaging script

**Files:**
- Create: `packaging/build_portable.ps1`

- [ ] **Step 1: Implement the minimal shared packager**

Add a fail-fast PowerShell script with these exact behaviors:

```powershell
[CmdletBinding()]
param(
    [string]$PortableDirectory = (Join-Path $env:RUNNER_TEMP "NexusSearch"),
    [string]$ArchivePath = (Join-Path $env:RUNNER_TEMP "NexusSearch-Windows-x64.zip")
)

$ErrorActionPreference = "Stop"
$dist = [IO.Path]::GetFullPath((Join-Path (Get-Location) "dist/nexussearch"))
$portable = [IO.Path]::GetFullPath($PortableDirectory)
$archive = [IO.Path]::GetFullPath($ArchivePath)

if (Test-Path $portable) { Remove-Item -Recurse -Force $portable }
if (Test-Path $archive) { Remove-Item -Force $archive }
Copy-Item -Recurse -Force $dist $portable
python packaging/prepare_portable.py $portable

foreach ($required_path in @(
    (Join-Path $portable "_internal/searx/engines/google.py"),
    (Join-Path $portable "_internal/searx/answerers/random.py"),
    (Join-Path $portable "_internal/searx/answerers/statistics.py"),
    (Join-Path $portable "settings.yml"),
    (Join-Path $portable "LICENSE"),
    (Join-Path $portable "AUTHORS.rst")
)) {
    if (-not (Test-Path $required_path)) { throw "required portable file missing: $required_path" }
}

$executable = Join-Path $portable "nexussearch.exe"
Remove-Item Env:SEARXNG_SETTINGS_PATH -ErrorAction SilentlyContinue
python packaging/smoke_test.py $executable --health-only
if ($LASTEXITCODE -ne 0) { throw "release settings health smoke failed: $LASTEXITCODE" }

$search_smoke_exit_code = 0
try {
    $env:SEARXNG_SETTINGS_PATH = Join-Path $portable "_internal/settings-smoke.yml"
    python packaging/smoke_test.py $executable
    $search_smoke_exit_code = $LASTEXITCODE
} finally {
    Remove-Item Env:SEARXNG_SETTINGS_PATH -ErrorAction SilentlyContinue
}
if ($search_smoke_exit_code -ne 0) { throw "deterministic search smoke failed: $search_smoke_exit_code" }

Compress-Archive -Path (Join-Path $portable "*") -DestinationPath $archive
Write-Host "Created $archive"
```

The resource checks must include the existing dynamically loaded SearXNG files and the license/provenance files already collected by `packaging/nexussearch.spec`.

- [ ] **Step 2: Run the focused contract tests and verify green**

Run:

```bash
python -m unittest tests.unit.test_windows_release_workflow -v
```

Expected: the packager-content test passes; the workflow tests remain red until both workflow files are updated.

### Task 3: Make development CI call the shared packager

**Files:**
- Modify: `.github/workflows/windows-portable.yml`

- [ ] **Step 1: Replace duplicated inline packaging behavior**

Keep the existing `push` and `pull_request` triggers, Python 3.12 setup, dependency installation, and PyInstaller build. Replace the current inline `Relocate and smoke-test package` and `Create portable archive` steps with one PowerShell step:

```yaml
      - name: Relocate, smoke-test, and archive package
        shell: pwsh
        run: pwsh packaging/build_portable.ps1
```

Keep the existing artifact upload, pointing to `${{ runner.temp }}/NexusSearch-Windows-x64.zip`. Do not add a release action or `contents: write` permission.

- [ ] **Step 2: Run the focused tests**

Run:

```bash
python -m unittest tests.unit.test_windows_release_workflow -v
```

Expected: the development workflow assertions pass; only the missing release workflow assertions fail.

### Task 4: Add the tag-only release workflow

**Files:**
- Create: `.github/workflows/windows-release.yml`

- [ ] **Step 1: Add the release workflow**

Create a workflow with this structure:

```yaml
name: Windows portable release

"on":
  push:
    tags: ["v*"]

permissions:
  contents: write

jobs:
  build-and-release:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          ref: ${{ github.ref }}
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install runtime and packaging dependencies
        run: python -m pip install --upgrade pip; python -m pip install -r requirements-windows.txt
      - name: Verify tagged commit
        shell: pwsh
        run: |
          $tag_commit = (git rev-list -n 1 "$env:GITHUB_REF_NAME").Trim()
          $checkout_commit = (git rev-parse HEAD).Trim()
          if ($tag_commit -ne $checkout_commit) { throw "checkout is not the tagged commit" }
      - name: Build onedir package
        run: python -m PyInstaller --noconfirm --clean packaging/nexussearch.spec
      - name: Relocate, smoke-test, and archive package
        shell: pwsh
        run: pwsh packaging/build_portable.ps1
      - name: Create SHA256 checksum
        shell: pwsh
        run: |
          $archive = Join-Path $env:RUNNER_TEMP "NexusSearch-Windows-x64.zip"
          $checksums = Join-Path $env:RUNNER_TEMP "SHA256SUMS.txt"
          $hash = (Get-FileHash -Algorithm SHA256 $archive).Hash.ToLowerInvariant()
          "$hash  NexusSearch-Windows-x64.zip" | Set-Content -Encoding ascii $checksums
      - name: Create GitHub Release
        shell: pwsh
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          gh release create "$env:GITHUB_REF_NAME" `
            --repo "$env:GITHUB_REPOSITORY" `
            --title "$env:GITHUB_REF_NAME" `
            --generate-notes `
            "$env:RUNNER_TEMP/NexusSearch-Windows-x64.zip" `
            "$env:RUNNER_TEMP/SHA256SUMS.txt"
```

The release job must have no branch or pull-request trigger. Every failure must stop before `gh release create` due to the fail-fast script and default action error handling.

- [ ] **Step 2: Run the focused tests and verify green**

Run:

```bash
python -m unittest tests.unit.test_windows_release_workflow -v
```

Expected: all workflow contract tests pass.

### Task 5: Document the downstream release coordinate

**Files:**
- Modify: `README.rst`

- [ ] **Step 1: Add release usage documentation**

Extend the existing Windows portable runtime section with a concise release contract that names the `v*` tag trigger and the exact assets:

```rst
Tagged releases
---------------

Version tags such as ``v0.1.0`` publish an immutable GitHub Release containing
``NexusSearch-Windows-x64.zip`` and ``SHA256SUMS.txt``. Downstream consumers
can pin the tag, download the fixed ZIP asset, and verify its SHA256 digest
before unpacking the portable runtime.
```

- [ ] **Step 2: Run documentation and contract checks**

Run:

```bash
python -m unittest tests.unit.test_windows_release_workflow tests.unit.test_portable_settings tests.unit.test_nexussearch_smoke -v
git diff --check
```

Expected: all selected tests pass and `git diff --check` produces no output.

### Task 6: Final verification and PR preparation

**Files:**
- Modify: none beyond the files above

- [ ] **Step 1: Run the repository's focused Python regression suite**

Run:

```bash
python -m unittest discover -s tests/unit -p 'test_*.py' -v
```

Expected: exit code 0 with no failed tests. Windows-specific packaging execution remains covered by the GitHub Actions workflow on `windows-latest`.

- [ ] **Step 2: Inspect the final diff and repository state**

Run:

```bash
git diff --check
git status --short
git diff --stat
git log --oneline origin/master..HEAD
```

Confirm the diff contains only the versioned release implementation, its tests, documentation, and the approved design/plan documents.

- [ ] **Step 3: Commit the implementation**

Run:

```bash
git add .github/workflows/windows-portable.yml .github/workflows/windows-release.yml packaging/build_portable.ps1 README.rst tests/unit/test_windows_release_workflow.py docs/superpowers/specs/2026-09-03-versioned-windows-releases-design.md docs/superpowers/plans/2026-09-03-versioned-windows-releases.md
git commit -m "ci: publish versioned Windows portable releases"
```

- [ ] **Step 4: Push the feature branch and open the pull request**

Create a branch containing the implementation if the current checkout is still on the issue-3 branch, push it to `origin`, and create a PR targeting the branch that contains the current portable CI baseline. Use a PR body that references issue #5 and includes the test commands and the note that the actual Windows build/smoke runs in Actions.
