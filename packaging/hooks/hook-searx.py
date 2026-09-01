"""Collect SearXNG's dynamically imported engines and package resources."""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = collect_submodules("searx.engines") + collect_submodules("searx.plugins")
datas = collect_data_files("searx", include_py_files=False)
