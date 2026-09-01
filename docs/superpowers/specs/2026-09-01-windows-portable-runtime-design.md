# Windows Portable NexusSearch Runtime Design

## Goal

Distribute the existing SearXNG fork as a Windows x64 PyInstaller onedir package that starts a localhost-only service without Docker, WSL, or a system Python installation.

## Design

`nexussearch.exe` will be a small launcher around the existing `searx.webapp:run` entry point. It will resolve a bundled or adjacent `settings.yml`, set `SEARXNG_SETTINGS_PATH`, and preserve SearXNG's existing request and search implementation. The packaged defaults bind to `127.0.0.1:8788`, enable JSON output, and avoid requiring Valkey for a single-user runtime.

The web app will expose `/health` as a stable JSON response while retaining `/healthz` for upstream compatibility. Existing `/search` behavior remains unchanged and is covered by a Flask test-client regression test.

The PyInstaller spec will collect Python packages plus runtime-loaded engines, templates, static files, translations, data files, CA certificates, configuration, and license/provenance files. A Windows workflow will build the onedir artifact, copy it to a clean temporary directory outside the checkout, run health and deterministic search smoke checks, terminate the process, and upload a zip.

## Verification

Unit tests will cover the health response and JSON search shape. The Windows workflow will verify relocation and process lifecycle. Linux-side checks will validate the spec and existing test suite without requiring a Windows runtime.

## Scope boundaries

No NexusMind integration, search redesign, onefile packaging, installer, updater, cache, or public deployment hardening is included.
