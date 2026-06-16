# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['file_accesser.py'],
    pathex=['C:\\msys64\\ucrt64\\bin'],
    binaries=[],
    datas=[('C:\\msys64\\ucrt64\\bin\\libstdc++-6.dll', '.'), ('build/main.exe', 'build'), ('build/Comparator.exe', 'build')],
    hiddenimports=['pydrive2.files', 'pydrive2.auth', 'pydrive2.drive', 'oauth2client', 'oauth2client.service_account', 'tqdm'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='file_accesser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='file_accesser',
)
