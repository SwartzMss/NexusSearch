# SPDX-License-Identifier: AGPL-3.0-or-later
"""Portable entry point for the NexusSearch Windows distribution."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def runtime_directory() -> Path:
    """Return the directory containing the executable or launcher source."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def configure_environment() -> Path:
    """Point SearXNG at the portable settings file when it is present."""
    base_directory = runtime_directory()
    candidates = (base_directory / "settings.yml", base_directory / "_internal" / "settings.yml")
    settings_path = next((path for path in candidates if path.is_file()), candidates[0])
    if settings_path.is_file():
        os.environ["SEARXNG_SETTINGS_PATH"] = str(settings_path)
    os.environ.setdefault("SEARXNG_DISABLE_ETC_SETTINGS", "true")
    return settings_path


def main() -> None:
    configure_environment()
    from searx.webapp import run

    run()


if __name__ == "__main__":
    main()
