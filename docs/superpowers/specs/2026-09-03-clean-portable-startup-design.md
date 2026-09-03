# Clean Portable Startup Design

## Goal

Make the Windows portable NexusSearch runtime start cleanly outside a Git checkout while preserving the localhost search backend contract.

## Architecture

Both Windows workflows will run `python -m searx.version freeze` immediately before PyInstaller. The existing SearXNG command will generate the ignored `searx/version_frozen.py` from the checked-out commit or release tag. The PyInstaller spec will explicitly include `searx.version_frozen` when that generated module exists, because `searx.version` imports it dynamically. The resulting onedir artifact will therefore load bundled metadata and will not need runtime Git commands. No `.git` directory will be packaged.

When a developer runs the source tree without freezing metadata, the existing SearXNG fallback remains unchanged.

## Portable configuration

Only `packaging/settings.yml` will override the upstream plugin configuration:

```yaml
plugins:
  searx.plugins.tracker_url_remover.SXNGPlugin:
    active: false
```

`searx/settings.yml` will remain untouched. Portable startup will therefore avoid initializing `TRACKER_PATTERNS` and fetching ClearURLs rules, while ordinary SearXNG installations retain their current defaults.

## Smoke and regression coverage

The existing portable smoke will continue to validate HTTP 200 JSON responses from `/health` and deterministic `/search?q=NVIDIA&format=json`. After stopping the child process, it will reject startup diagnostics containing Git checkout failures, version/Git URL lookup errors, or ClearURLs tracker-rule fetch errors. Failure output will include captured stdout and stderr.

Unit tests will verify:

- portable settings explicitly disable the tracker URL remover;
- the upstream settings file remains unchanged at that setting;
- both Windows workflows freeze version metadata before building;
- the PyInstaller spec includes the generated frozen module;
- the smoke validator rejects the prohibited startup diagnostics while retaining existing health/search checks.

The test suite will not contact the ClearURLs endpoint.

## Error handling

The freeze step fails the Windows build if metadata generation fails. The spec only references the frozen module when it exists, preserving source-tree builds that have not run freeze. Portable smoke treats any prohibited startup diagnostic as a failure and reports the full child-process logs for diagnosis.

## Acceptance criteria

- Portable builds use bundled version/repository metadata outside Git.
- Portable configuration disables only the tracker URL remover.
- No expected Git or ClearURLs startup warning appears in the standard smoke path.
- `/health` and deterministic JSON `/search` continue to pass.
- Windows CI remains PyInstaller `onedir` and does not package `.git`.
