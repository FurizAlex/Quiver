import os
import glob

themeModules = [
    f"themes.{os.path.splitext(os.path.basename(f))[0]}"
    for f in glob.glob("themes/*.py")
    if not os.path.basename(f).startswith("__")
]


a = Analysis(
    ['frontend/qt/app.py'],
    pathex=['.'],
    binaries=[],
    datas=[
		('assets', 'assets'),
		('themes', 'themes'),
		('docs', 'docs'),
		('config', 'config'),
	],
    hiddenimports=[
		'frontend',
		'frontend.qt',
		'core',
		'commands',
		'input',
		'ui',
		'syntax',
		'util',
		'config',
	] + themeModules,
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
    name='Quiver',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
	icon='assets/icons/quiver.png',
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
    name='Quiver',
)
