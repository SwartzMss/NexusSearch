# NexusSearch CI Surface Design

## Goal

Reduce inherited SearXNG GitHub Actions to the CI that protects NexusSearch's
supported runtime and Windows portable distribution.

## Scope

The product CI surface will contain only:

- `.github/workflows/integration.yml` for core Python lint and regression tests.
- `.github/workflows/windows-portable.yml` for the Windows x64 portable build,
  relocation checks, runtime smoke tests, and artifact creation.

The upstream-only container, data-update, documentation, localization, and AI
policy workflows will be removed. NexusSearch does not publish those upstream
artifacts, use those upstream secrets, or run those upstream maintenance bots.

## Integration workflow

The Integration workflow will use two lanes:

- Python 3.12: install the project and run the complete `make V=1 ci.test`
  target, which remains the primary supported lane and matches the Windows
  packaging interpreter.
- Python 3.14: install the project and run the same test target as an upstream
  compatibility signal.

The Theme job will be removed because NexusSearch's release-critical surface is
the headless/API search runtime and Windows portable executable, not independent
SearXNG theme publishing.

## Failure and ownership boundaries

Each retained workflow remains responsible for its own product behavior. The
Integration workflow does not build containers or publish documentation; the
Windows workflow does not depend on external search services. Future upstream
syncs are covered by the two Python regression lanes plus the frozen Windows
startup, relocation, and deterministic search checks.

## Verification

Before opening the implementation PR, validate that:

1. Only `integration.yml` and `windows-portable.yml` remain under
   `.github/workflows/`.
2. Integration's matrix contains exactly Python 3.12 and 3.14 and no Theme job.
3. Workflow YAML parses and passes repository YAML lint where available.
4. The retained workflow files have no whitespace errors.
