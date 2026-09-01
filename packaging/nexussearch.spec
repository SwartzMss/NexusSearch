# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

root = Path(SPECPATH).parent
searx_datas = collect_data_files("searx", include_py_files=False)
certifi_datas = collect_data_files("certifi", include_py_files=False)
engine_sources = [(str(path), "searx/engines") for path in (root / "searx" / "engines").glob("*.py")]
answerer_sources = [(str(path), "searx/answerers") for path in (root / "searx" / "answerers").glob("*.py")]
datas = searx_datas + [
    *certifi_datas,
    *engine_sources,
    *answerer_sources,
    (str(root / "packaging" / "settings.yml"), "."),
    (str(root / "packaging" / "settings-smoke.yml"), "."),
    (str(root / "LICENSE"), "."),
    (str(root / "AUTHORS.rst"), "."),
]
hiddenimports = (
    collect_submodules("searx.engines")
    + collect_submodules("searx.answerers")
    + collect_submodules("searx.plugins")
)

a = Analysis(
    [str(root / "nexussearch_launcher.py")],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[str(root / "packaging" / "hooks")],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], [], [], name="nexussearch", console=True)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="nexussearch")
