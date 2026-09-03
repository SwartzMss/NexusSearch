# Versioned Windows Portable Releases Design

## Goal

Publish the existing NexusSearch Windows x64 portable runtime as immutable,
versioned GitHub Release assets that downstream projects can pin by tag, stable
asset name, and SHA256 digest.

## Architecture

The existing `windows-portable.yml` workflow remains the development CI entry
point for the portable runtime. Its inline relocation, resource checks, health
smoke, deterministic search smoke, and archive creation steps move into
`packaging/build_portable.ps1`, so CI and release publication execute the same
packaging contract.

A new `windows-release.yml` workflow triggers only for pushed tags matching
`v*`. It checks out the tag commit, installs the same Windows build
dependencies, builds the existing PyInstaller `onedir` specification, invokes
the shared packaging script, creates `SHA256SUMS.txt` for the fixed ZIP name,
and creates a GitHub Release with both files. The release job has
`contents: write` permission; the development workflow has no release-writing
permission or release steps.

## Shared packaging contract

`packaging/build_portable.ps1` will:

1. Copy `dist/nexussearch` to a clean directory outside the checkout.
2. Run `prepare_portable.py` to expose the bundled `settings.yml` beside the
   executable.
3. Verify the dynamically loaded Google engine and required answerer modules
   are present, and verify the release settings file exists.
4. Run `smoke_test.py --health-only` with the real release configuration.
5. Run `smoke_test.py` with `_internal/settings-smoke.yml` selected so `/search`
   is deterministic and offline.
6. Remove the temporary settings override and create
   `NexusSearch-Windows-x64.zip`.

The script fails fast on any missing resource or smoke failure. The existing
PyInstaller specification remains the single source of truth for runtime
contents, including license and provenance files.

## Release asset and provenance contract

Every successful `v*` tag run publishes exactly these stable asset names:

- `NexusSearch-Windows-x64.zip`
- `SHA256SUMS.txt`

The checksum file uses the conventional two-space-separated SHA256 digest and
filename format. The release title and tag are both the pushed version tag, and
the build verifies that the checked-out commit is the commit addressed by that
tag before packaging.

## Error handling and safety

- Any build, relocation, resource check, smoke test, checksum generation, or
  release command failure stops the workflow before publication.
- Release publication is impossible from ordinary branch pushes or pull
  requests because the release workflow has a `v*` tag trigger only.
- Existing CI continues to upload a diagnostic artifact for branch/PR use and
  does not create releases.

## Verification

Linux-side tests will cover the shared workflow contract through YAML/text
assertions: the development workflow invokes the shared script, the release
workflow has only the version-tag trigger and write permission, both workflows
use the existing PyInstaller spec, and the stable asset/checksum names are
present. The existing Python unit tests remain the regression suite for the
portable settings and smoke behavior. GitHub Actions on `windows-latest` is
the execution environment for the real packaging and runtime smoke checks.

## Out of scope

NexusMind integration, process supervision, API changes, new search engines,
ranking changes, onefile packaging, installers, auto-update, code signing, and
public deployment remain out of scope.
