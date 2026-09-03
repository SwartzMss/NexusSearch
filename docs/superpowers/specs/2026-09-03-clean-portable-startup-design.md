# Clean Portable Startup Design

## Goal

Make the Windows portable NexusSearch runtime start cleanly outside a Git checkout while preserving the localhost search backend contract.

## Architecture

Both Windows workflows will run `python -m searx.version freeze` immediately before PyInstaller. The existing SearXNG command will generate the ignored `searx/version_frozen.py` from the checked-out commit or release tag. The PyInstaller spec will explicitly include `searx.version_frozen` when that generated module exists, because `searx.version` imports it dynamically. The resulting onedir artifact will therefore load bundled metadata and will not need runtime Git commands. No `.git` directory will be packaged.

When a developer runs the source tree without freezing metadata, the existing SearXNG fallback remains unchanged.

## Portable configuration

The two portable configurations, `packaging/settings.yml` and
`packaging/settings-smoke.yml`, will preserve the upstream plugin entries except
for the tracker URL remover, which is deliberately omitted:

```yaml
plugins:
  # Keep the upstream plugin entries here, but omit tracker_url_remover.
```

`searx/settings.yml` will remain untouched. Because SearXNG replaces the
`plugins` mapping when a user configuration supplies it, both portable files
must list the other upstream plugins explicitly to preserve their behavior.
Omitting tracker_url_remover means portable startup never constructs or
initializes it, so it avoids fetching ClearURLs rules while ordinary SearXNG
installations retain their current defaults.

## Smoke and regression coverage

The existing portable smoke will continue to validate HTTP 200 JSON responses from `/health` and deterministic `/search?q=NVIDIA&format=json`. After stopping the child process, it will reject startup diagnostics containing Git checkout failures, version/Git URL lookup errors, or ClearURLs tracker-rule fetch errors. Failure output will include captured stdout and stderr.

Unit tests will verify:

- portable settings preserve the upstream plugin set except for tracker URL remover;
- loading either portable plugin set does not call `TRACKER_PATTERNS.init()`;
- the upstream settings file remains unchanged at that setting;
- both Windows workflows freeze version metadata before building;
- the PyInstaller spec includes the generated frozen module;
- the smoke validator rejects the prohibited startup diagnostics while retaining existing health/search checks.

The test suite will not contact the ClearURLs endpoint.

## Error handling

The freeze step fails the Windows build if metadata generation fails. The spec only references the frozen module when it exists, preserving source-tree builds that have not run freeze. Portable smoke treats Git lookup errors and all ClearURLs fetch failure variants as prohibited diagnostics and reports the full child-process logs for diagnosis.

## Acceptance criteria

- Portable builds use bundled version/repository metadata outside Git.
- Portable configuration disables only the tracker URL remover.
- No expected Git or ClearURLs startup warning appears in the standard smoke path.
- `/health` and deterministic JSON `/search` continue to pass.
- Windows CI remains PyInstaller `onedir` and does not package `.git`.
