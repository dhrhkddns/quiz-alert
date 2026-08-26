# -*- mode: python ; coding: utf-8 -*-
# 빌드: pyinstaller --noconfirm quiz_alert.spec

a = Analysis(
    ["quiz_alert.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("questions.json", "."),
        ("exam_images", "exam_images"),
    ],
    hiddenimports=["app_paths", "mini_tips", "pixel_art", "PIL", "PIL.Image", "PIL.ImageTk"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="QuizAlert",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
