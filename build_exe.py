"""
StudyTutorAI - PyInstaller Build Script (Fixed)
"""
import sys, os, shutil, subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DIST_DIR = PROJECT_ROOT / "dist"


def check_dependencies():
    """Check required dependencies"""
    for pkg in ["transformers", "torch", "gradio"]:
        r = subprocess.run(
            [sys.executable, "-m", "pip", "show", pkg],
            capture_output=True, text=True
        )
        if r.returncode != 0:
            print(f"[WARN] Missing: {pkg}")
            return False
        print(f"  OK {pkg}")
    return True


def write_spec():
    """Write PyInstaller SPEC file with proper data collection"""
    content = '''# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.building.build_main import Analysis, PYZ, EXE
from PyInstaller.utils.hooks import collect_data_files, copy_metadata
from pathlib import Path

block_cipher = None
PROJECT_ROOT = Path(r"C:\\Users\\iMac\\.qclaw\\workspace-ua58rsb93veqtxl7\\study-tutor-ai")

# Collect Gradio and safehttpx data files
datas = [
    (str(PROJECT_ROOT / "models"), "models"),
    (str(PROJECT_ROOT / "config"), "config"),
]

# Gradio needs its static files
try:
    datas += collect_data_files("gradio")
except Exception:
    pass

# safehttpx needs version.txt
try:
    datas += collect_data_files("safehttpx")
except Exception:
    pass

# Also collect any json/schema files
try:
    datas += collect_data_files("gradio_client")
except Exception:
    pass

hiddenimports = [
    "gradio",
    "safehttpx",
    "gradio_client",
    "gradio.blocks",
    "gradio.interface",
    "gradio.layouts",
    "gradio.components",
    "gradio.events",
    "gradio.themes",
    "gradio.themes.soft",
    "torch", "torch.nn",
    "transformers",
    "transformers.models.qwen2",
    "faiss",
    "sentence_transformers",
    "pypdf",
    "PIL", "PIL.Image",
    "psutil", "numpy",
    "fastapi", "starlette",
    "httpx", "httpcore",
    "anyio", "anyio._backends",
    "websockets",
]

excludes = [
    "matplotlib", "mpl_toolkits", "scipy",
    "sklearn", "pandas",
    "PyQt5", "PyQt6", "PySide6",
    "ipython", "jupyter",
    "tkinter",
]

a = Analysis(
    [str(PROJECT_ROOT / "run.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries + a.zipfiles + a.datas,
    [],
    name="StudyTutorAI",
    debug=False,
    strip=False,
    upx=False,
    console=True,  # Enable console for debugging
    icon=None,
)
'''

    spec_path = PROJECT_ROOT / "study_tutor.spec"
    spec_path.write_text(content, encoding="utf-8")
    print(f"  SPEC: {spec_path}")
    return spec_path


def build_exe():
    """Run PyInstaller"""
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    print("=" * 50)
    print("[Build] StudyTutorAI Packaging...")
    print("=" * 50)

    spec_path = write_spec()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--distpath", str(DIST_DIR),
        "--workpath", str(PROJECT_ROOT / "build"),
        "--clean",
        str(spec_path),
    ]

    result = subprocess.run(cmd)

    if result.returncode == 0:
        exe_path = DIST_DIR / "StudyTutorAI.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / 1024 / 1024
            print(f"\n[PASS] Build complete!")
            print(f"  Output: {DIST_DIR.resolve()}")
            print(f"  EXE:    {exe_path.resolve()}")
            print(f"  Size:   {size_mb:.1f} MB")
        else:
            print(f"\n[PASS] Build complete! See: {DIST_DIR.resolve()}")
    else:
        print(f"\n[FAIL] Build failed (exit {result.returncode})")
        sys.exit(result.returncode)


if __name__ == "__main__":
    if not check_dependencies():
        sys.exit(1)
    build_exe()