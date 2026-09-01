# Windows Portable NexusSearch Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build and smoke-test a relocatable Windows x64 SearXNG onedir runtime.

**Architecture:** Keep SearXNG search internals intact, add a launcher/config adapter, expose a JSON health endpoint, and package all runtime resources through PyInstaller hooks/specification.

**Tech Stack:** Python 3.10+, Flask, PyInstaller, GitHub Actions, pytest/unittest.

---

### Task 1: Health and JSON API regression coverage

**Files:** `tests/unit/test_webapp.py`, `searx/webapp.py`

- [ ] Add tests asserting `GET /health` returns 200, JSON content type, and `{"status": "ok"}`.
- [ ] Add a test asserting `/healthz` remains 200 for compatibility.
- [ ] Add/retain JSON search assertions for title, url, content, and engine fields using the existing mocked search fixture.
- [ ] Run the focused tests and observe the new health test fail before implementation.
- [ ] Add the minimal `/health` Flask route and run the focused tests again.

### Task 2: Portable launcher and default configuration

**Files:** `nexussearch_launcher.py`, `packaging/settings.yml`, `tests/unit/test_nexussearch_launcher.py`, `requirements-windows.txt`

- [ ] Write tests for locating a config beside a frozen executable and for setting `SEARXNG_SETTINGS_PATH` before delegating to `searx.webapp.run`.
- [ ] Implement a launcher that uses `sys.executable` when frozen, its parent otherwise, and calls the existing `run` function.
- [ ] Add portable defaults with localhost binding, port 8788, JSON format, and no required Valkey service.
- [ ] Run launcher tests and existing settings tests.

### Task 3: PyInstaller onedir specification

**Files:** `packaging/nexussearch.spec`, `packaging/hooks/hook-searx.py`, `requirements-windows.txt`, `requirements-dev.txt`

- [ ] Add PyInstaller as a Windows build dependency.
- [ ] Define an onedir spec using `collect_submodules('searx.engines')`, `collect_data_files('searx')`, and explicit adjacent settings/license data.
- [ ] Add a hook for dynamic SearXNG engine imports and package data.
- [ ] Validate the spec parses on Linux and document the resulting artifact layout.

### Task 4: Windows build and relocation smoke workflow

**Files:** `.github/workflows/windows-portable.yml`, `packaging/smoke_test.py`, `README.rst`

- [ ] Add a Windows x64 workflow that installs dependencies, runs PyInstaller, copies the output to `${{ runner.temp }}`, launches the exe, polls `/health`, and checks JSON `/search` shape.
- [ ] Make the smoke script terminate the child process in a `finally` block and fail on timeout, non-200 responses, invalid JSON, or missing required keys.
- [ ] Zip and upload the relocated package, preserving license/provenance files.
- [ ] Document local build and runtime usage.

### Task 5: Verification and handoff

- [ ] Run focused unit tests, then the available full test suite.
- [ ] Run `git diff --check` and validate workflow/spec syntax.
- [ ] Review acceptance criteria against changed files and commit the implementation.
