# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prepare the writable, user-facing files in a PyInstaller onedir package."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def ensure_portable_settings(package_directory: Path) -> Path:
    """Copy the bundled settings file next to the executable if needed."""
    root_settings = package_directory / "settings.yml"
    if root_settings.is_file():
        return root_settings
    internal_settings = package_directory / "_internal" / "settings.yml"
    if not internal_settings.is_file():
        raise FileNotFoundError(f"bundled settings not found in {package_directory}")
    shutil.copy2(internal_settings, root_settings)
    return root_settings


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: prepare_portable.py PACKAGE_DIRECTORY")
    ensure_portable_settings(Path(sys.argv[1]).resolve())
