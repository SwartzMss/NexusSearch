# Clean Portable Startup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Windows PyInstaller portable runtime use bundled SearXNG version metadata, skip the unnecessary tracker-rule fetch, and prove clean startup without changing the NexusSearch HTTP contract.

**Architecture:** The Windows workflows generate `searx/version_frozen.py` immediately before PyInstaller. The spec explicitly includes that dynamic-import module when present, while both portable settings files preserve the upstream plugin set except for the omitted tracker URL remover. The existing relocated portable smoke gains deterministic log assertions in addition to its `/health` and JSON `/search` checks.

**Tech Stack:** Python 3.10/3.12, unittest/nose2, PyYAML, PyInstaller, GitHub Actions YAML, PowerShell.

---

### Task 1: Add regression tests for the portable configurations

**Files:**
- Modify: `tests/unit/test_portable_settings.py`
- Test target: `packaging/settings.yml`, `packaging/settings-smoke.yml`, and `searx/settings.yml`

- [ ] **Step 1: Write the failing tests**

Add these methods to `PortableSettingsTestCase`:

```python
    def test_portable_configs_exclude_tracker_and_preserve_plugins(self):
        """Portable configs omit only the plugin that fetches tracker rules."""
        upstream = yaml.safe_load((ROOT / "searx/settings.yml").read_text(encoding="utf-8"))
        tracker_plugin = "searx.plugins.tracker_url_remover.SXNGPlugin"
        expected_plugins = set(upstream["plugins"]) - {tracker_plugin}
        for relative_path in ("packaging/settings.yml", "packaging/settings-smoke.yml"):
            settings = yaml.safe_load((ROOT / relative_path).read_text(encoding="utf-8"))
            self.assertEqual(set(settings["plugins"]), expected_plugins, relative_path)

    def test_portable_configs_do_not_initialize_tracker_patterns(self):
        """Loading either portable plugin set never initializes tracker rules."""
        from searx import data
        from searx.plugins import PluginStorage

        for relative_path in ("packaging/settings.yml", "packaging/settings-smoke.yml"):
            settings = yaml.safe_load((ROOT / relative_path).read_text(encoding="utf-8"))
            storage = PluginStorage()
            with patch.object(data.TRACKER_PATTERNS, "init") as tracker_init:
                storage.load_settings(settings["plugins"])
                storage.init(Mock())
                tracker_init.assert_not_called()

    def test_upstream_config_keeps_tracker_url_remover_enabled(self):
        """The upstream SearXNG default remains unchanged."""
        settings = yaml.safe_load((ROOT / "searx/settings.yml").read_text(encoding="utf-8"))
        plugin = settings["plugins"]["searx.plugins.tracker_url_remover.SXNGPlugin"]
        self.assertTrue(plugin["active"])
```

- [ ] **Step 2: Run the focused tests and verify the intended failure**

Run:

```bash
PYTHONPATH=. .venv/bin/python -m nose2 -v tests.unit.test_portable_settings
```

Expected: the existing two tests pass; the plugin-set test fails because the portable files do not yet list the upstream plugins, and the no-initialization test fails because the current release config still includes the tracker entry.

- [ ] **Step 3: Implement the minimal configuration change**

Set the `plugins` mapping in both portable files to the upstream entries from
`searx/settings.yml`, excluding only the tracker URL remover. Preserve every
other plugin entry and its existing `active` value, and add a comment explaining
that the tracker entry is deliberately omitted.

```yaml
plugins:
  searx.plugins.calculator.SXNGPlugin:
    active: true
  searx.plugins.infinite_scroll.SXNGPlugin:
    active: false
  searx.plugins.hash_plugin.SXNGPlugin:
    active: true
  searx.plugins.self_info.SXNGPlugin:
    active: true
  searx.plugins.unit_converter.SXNGPlugin:
    active: true
  searx.plugins.ahmia_filter.SXNGPlugin:
    active: true
  searx.plugins.hostnames.SXNGPlugin:
    active: true
  searx.plugins.time_zone.SXNGPlugin:
    active: true
  searx.plugins.oa_doi_rewrite.SXNGPlugin:
    active: false
  searx.plugins.tor_check.SXNGPlugin:
    active: false
  # omit searx.plugins.tracker_url_remover.SXNGPlugin
```

Do not edit `searx/settings.yml`.

- [ ] **Step 4: Run the focused tests and verify they pass**

Run the same nose2 command. Expected: 5 tests pass with zero failures.

- [ ] **Step 5: Commit the task**

```bash
git add packaging/settings.yml packaging/settings-smoke.yml tests/unit/test_portable_settings.py
git commit -m "fix: disable tracker fetch in portable settings"
```

### Task 2: Add failing tests for frozen metadata packaging

**Files:**
- Modify: `tests/unit/test_windows_release_workflow.py`
- Inspect: `.github/workflows/windows-portable.yml`, `.github/workflows/windows-release.yml`, `packaging/nexussearch.spec`

- [ ] **Step 1: Write the failing workflow/spec contract tests**

Add these methods to `WindowsReleaseWorkflowTestCase`:

```python
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
            freeze_index = next(
                i for i, run in enumerate(run_steps) if "python -m searx.version freeze" in run
            )
            build_index = next(
                i for i, run in enumerate(run_steps) if "packaging/nexussearch.spec" in run
            )
            self.assertLess(freeze_index, build_index, relative_path)

    def test_spec_bundles_frozen_version_module(self):
        """PyInstaller includes the dynamically imported frozen module."""
        spec = read_text("packaging/nexussearch.spec")
        self.assertIn("version_frozen.py", spec)
        self.assertIn("searx.version_frozen", spec)
```

- [ ] **Step 2: Run the focused tests and verify the intended failure**

Run:

```bash
PYTHONPATH=. .venv/bin/python -m nose2 -v tests.unit.test_windows_release_workflow
```

Expected: the existing workflow tests pass and the two new tests fail because the workflows do not freeze metadata and the spec has no frozen-module entry.

- [ ] **Step 3: Commit only the test additions**

```bash
git add tests/unit/test_windows_release_workflow.py
git commit -m "test: cover frozen portable version metadata"
```

### Task 3: Implement frozen version metadata in the build

**Files:**
- Modify: `.github/workflows/windows-portable.yml`
- Modify: `.github/workflows/windows-release.yml`
- Modify: `packaging/nexussearch.spec`
- Test: `tests/unit/test_windows_release_workflow.py`

- [ ] **Step 1: Add the workflow freeze step**

Insert this step directly before `Build onedir package` in both workflows:

```yaml
      - name: Freeze runtime version metadata
        run: python -m searx.version freeze
```

The existing checkout remains available for the command to derive metadata. The release workflow derives the version from the checked-out tag; the pull-request workflow derives metadata from the CI context.

- [ ] **Step 2: Add conditional dynamic-module inclusion to the spec**

Replace the tuple assignment for `hiddenimports` with a list and append the generated module only when it exists:

```python
hiddenimports = [
    *collect_submodules("searx.engines"),
    *collect_submodules("searx.answerers"),
    *collect_submodules("searx.plugins"),
]
if (root / "searx" / "version_frozen.py").is_file():
    hiddenimports.append("searx.version_frozen")
```

This lets the CI artifact import the bundled module while keeping an unfrozen local source build understandable.

- [ ] **Step 3: Run the focused tests and verify they pass**

Run:

```bash
PYTHONPATH=. .venv/bin/python -m nose2 -v tests.unit.test_windows_release_workflow
```

Expected: all workflow/spec contract tests pass.

- [ ] **Step 4: Commit the implementation**

```bash
git add .github/workflows/windows-portable.yml .github/workflows/windows-release.yml packaging/nexussearch.spec
git commit -m "fix: bundle frozen version metadata in Windows builds"
```

### Task 4: Add failing tests for clean startup diagnostics

**Files:**
- Modify: `tests/unit/test_nexussearch_smoke.py`
- Test target: `packaging/smoke_test.py`

- [ ] **Step 1: Write the failing diagnostic tests**

Add these methods to `SmokeTestCase`:

```python
    def test_prohibited_git_diagnostic_is_rejected(self):
        """Portable startup must not invoke Git from outside a checkout."""
        with self.assertRaisesRegex(RuntimeError, "not a git repository"):
            smoke.validate_startup_diagnostics("fatal: not a git repository")

    def test_prohibited_clearurls_diagnostic_is_rejected(self):
        """Portable startup must not fetch ClearURLs rules."""
        with self.assertRaisesRegex(RuntimeError, "rules1.clearurls.xyz"):
            smoke.validate_startup_diagnostics(
                "TRACKER_PATTERNS: HTTPError (https://rules1.clearurls.xyz/data.minify.json) occured while fetching Timeout"
            )

    def test_clean_startup_diagnostics_are_accepted(self):
        """Unrelated normal output is not rejected by the startup guard."""
        smoke.validate_startup_diagnostics("INFO:searx: version: 0.1.0\\n")
```

- [ ] **Step 2: Run the focused tests and verify the intended failure**

Run:

```bash
PYTHONPATH=. .venv/bin/python -m nose2 -v tests.unit.test_nexussearch_smoke
```

Expected: the existing smoke tests pass and the two rejection tests fail with `AttributeError` because the validator does not exist; the clean-output test also fails for the same missing function.

- [ ] **Step 3: Implement the diagnostic validator**

Add this constant and function to `packaging/smoke_test.py`:

```python
PROHIBITED_STARTUP_DIAGNOSTICS = (
    "not a git repository",
    "Error while getting the version:",
    "Error while getting the git URL & branch:",
    "rules1.clearurls.xyz/data.minify.json",
    "TRACKER_PATTERNS: HTTPError",
    "TRACKER_PATTERNS: ClearURL ignore HTTP",
    "TRACKER_PATTERNS: failed fetching ClearURL rule lists",
)


def validate_startup_diagnostics(diagnostics: str) -> None:
    """Reject expected Git and ClearURLs failures from a portable startup."""
    for diagnostic in PROHIBITED_STARTUP_DIAGNOSTICS:
        if diagnostic in diagnostics:
            raise RuntimeError(f"portable startup emitted prohibited diagnostic: {diagnostic}")
```

After `stop_process` returns in `main`, validate the captured diagnostics before deciding whether the smoke succeeded:

```python
        diagnostics = stop_process(process, stdout_file, stderr_file, stdout_path, stderr_path)
        if smoke_error is None:
            try:
                validate_startup_diagnostics(diagnostics)
            except RuntimeError as error:
                smoke_error = error
        if smoke_error is not None:
            raise RuntimeError(f"{smoke_error}\\n\\n{diagnostics}") from smoke_error
        return 0
```

- [ ] **Step 4: Run the focused tests and verify they pass**

Run the same nose2 command. Expected: all smoke tests pass.

- [ ] **Step 5: Commit the implementation**

```bash
git add packaging/smoke_test.py tests/unit/test_nexussearch_smoke.py
git commit -m "test: reject noisy portable startup diagnostics"
```

### Task 5: Run the complete relevant verification suite

**Files:**
- Inspect: all files changed in Tasks 1-4

- [ ] **Step 1: Run all relevant unit tests**

Run:

```bash
PYTHONPATH=. .venv/bin/python -m nose2 -v tests.unit.test_portable_settings tests.unit.test_nexussearch_launcher tests.unit.test_nexussearch_smoke tests.unit.test_windows_release_workflow
```

Expected: 23 tests pass with zero failures and errors.

- [ ] **Step 2: Run the broader unit suite**

Run:

```bash
PYTHONPATH=. .venv/bin/python -m nose2 -v tests.unit
```

Expected: the repository unit suite passes. If unrelated optional dependencies are missing, record the exact failing modules and run the affected relevant tests independently.

- [ ] **Step 3: Check formatting and the final diff**

Run:

```bash
git diff --check
git status --short
git diff --stat origin/master...HEAD
```

Expected: no whitespace errors, only issue #7 files plus the committed spec/plan are present, and no `.git` or generated `searx/version_frozen.py` file is staged.

- [ ] **Step 4: Commit any only-needed cleanup**

If the verification reveals a formatting-only issue in the changed files, fix it with `apply_patch`, rerun the affected tests, and commit:

```bash
git add .github/workflows/windows-portable.yml .github/workflows/windows-release.yml packaging/nexussearch.spec packaging/settings.yml packaging/smoke_test.py tests/unit/test_nexussearch_smoke.py tests/unit/test_portable_settings.py tests/unit/test_windows_release_workflow.py
git commit -m "chore: tidy portable startup validation"
```

Do not add unrelated refactors or generated artifacts.

### Task 6: Review, push, and open the pull request

**Files:**
- Inspect: complete branch diff and test output

- [ ] **Step 1: Request a code review of the branch diff**

Compare `origin/master` with `HEAD` and review specifically for issue #7 acceptance criteria: frozen metadata inclusion, portable-only tracker disablement, no startup warning assertions, unchanged HTTP smoke behavior, onedir packaging, and no `.git` packaging.

- [ ] **Step 2: Push the feature branch**

```bash
git push -u origin issue-7-clean-portable-startup
```

- [ ] **Step 3: Create the PR linked to issue #7**

```bash
gh pr create --repo SwartzMss/NexusSearch --base master --head issue-7-clean-portable-startup --title "fix: clean portable startup outside Git" --body-file /tmp/nexussearch-issue-7-pr.md
```

The PR body must summarize the frozen metadata build step, portable-only tracker plugin disablement, smoke log assertions, and test commands, and include `Closes #7`.

- [ ] **Step 4: Verify the created PR**

```bash
gh pr view --repo SwartzMss/NexusSearch --json number,url,title,baseRefName,headRefName,state
```

Expected: an open PR targeting `master` from `issue-7-clean-portable-startup`, linked to issue #7.
