# NexusSearch CI Surface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce GitHub Actions to core Integration regression coverage and the Windows portable runtime workflow.

**Architecture:** Keep the existing Integration workflow as the single cross-platform Python regression entry point, with Python 3.12 as the primary lane and Python 3.14 as the compatibility lane. Remove upstream-only workflows and the non-release-critical Theme job; leave the Windows portable workflow responsible for frozen-package build, relocation, runtime, and artifact checks.

**Tech Stack:** GitHub Actions YAML, Make targets, Python 3.12/3.14, repository YAML/lint tooling.

---

### Task 1: Remove inherited upstream workflows

**Files:**
- Delete: `.github/workflows/container.yml`
- Delete: `.github/workflows/data-update.yml`
- Delete: `.github/workflows/documentation.yml`
- Delete: `.github/workflows/l10n.yml`
- Delete: `.github/workflows/ai-policy.yml`

- [x] **Step 1: Confirm the deletion targets are exactly the upstream-only workflows.**

  Run `rg --files .github/workflows | sort` and verify the five listed files are present alongside `integration.yml` and `windows-portable.yml`.

- [x] **Step 2: Delete only the five listed workflow files.**

  Use `apply_patch` deletion patches for the exact paths; do not alter scripts, secrets, or product code.

- [x] **Step 3: Verify the workflow directory contains only the two retained product workflows.**

  Run `test "$(find .github/workflows -maxdepth 1 -type f -name '*.yml' | wc -l)" -eq 2` and inspect the sorted file list.

### Task 2: Simplify Integration CI

**Files:**
- Modify: `.github/workflows/integration.yml`

- [x] **Step 1: Reduce the Python matrix to the supported lanes.**

  Replace the four matrix entries with exactly:

  ```yaml
          - "3.12"
          - "3.14"
  ```

- [x] **Step 2: Remove the Theme job in full.**

  Delete the `theme` job and all of its Node.js setup, theme lint, and theme build steps. Keep the `test` job's install and `make V=1 ci.test` command unchanged.

- [x] **Step 3: Verify the retained workflow structure.**

  Parse the file with `python3` and PyYAML, then assert the matrix is `['3.12', '3.14']`, the only job key is `test`, and the test command still contains `make V=1 ci.test`.

### Task 3: Validate and hand off

**Files:**
- Verify: `.github/workflows/integration.yml`
- Verify: `.github/workflows/windows-portable.yml`
- Verify: `docs/superpowers/specs/2026-09-01-ci-surface-design.md`

- [x] **Step 1: Run repository-local static checks.**

  Run `git diff --check` and a Python YAML parse over both retained workflow files. If `yamllint` is installed, run it against both files; otherwise record that the executable is unavailable.

- [x] **Step 2: Inspect the final diff for scope.**

  Run `git status --short`, `git diff --stat`, and `git diff -- .github/workflows` to confirm only workflow cleanup plus the implementation plan/spec changed.

- [x] **Step 3: Commit the implementation.**

  Run `git add .github/workflows docs/superpowers/plans/2026-09-01-ci-surface.md` and commit with `ci: simplify NexusSearch workflows`.

- [x] **Step 4: Push and verify CI starts.**

  Push the current branch and run `gh pr checks` or inspect the associated Actions run. Confirm the deleted workflows no longer appear and the retained Integration/Windows checks are queued.
