# -----------------------------------------------------------------------------
# PyInstaller spec file for fast-print
# Build with: uv run pyinstaller app.spec
# Output: dist/FastPrint/FastPrint.exe
# -----------------------------------------------------------------------------

from PyInstaller.utils.hooks import collect_all, collect_submodules
from PyInstaller.compat import is_win
import os
import sys

# -----------------------------------------------------------------------------
# Paths / Constants
# -----------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.abspath(SPEC))

APP_NAME = "FastPrint"
ENTRYPOINT = os.path.join(ROOT, "src", "ui", "gui.py")

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

def find_python_base() -> str:
    """
    Resolves the base Python directory even when running inside a venv (uv).
    Locates hardware DLLs consistently.
    """
    python_dir = os.path.dirname(sys.executable)
    # uv venv layout: .venv/Scripts/python.exe -> Up 2 levels to project root
    candidate = os.path.abspath(os.path.join(python_dir, "..", ".."))

    if not os.path.exists(os.path.join(candidate, "DLLs")):
        candidate = python_dir

    return candidate


def find_dll(dlls_dir: str, python_base: str, name: str):
    """Returns a PyInstaller binaries tuple list: [(src, ".")]"""
    candidate1 = os.path.join(dlls_dir, name)
    if os.path.exists(candidate1):
        return [(candidate1, ".")]

    candidate2 = os.path.join(python_base, name)
    if os.path.exists(candidate2):
        return [(candidate2, ".")]

    return []


def collect_ctypes_dependencies():
    """
    Bypasses missing DLL errors caused by hardware Spooler and low-level Win32 hooks.
    """
    python_base = find_python_base()
    dlls_dir = os.path.join(python_base, "DLLs")

    binaries = []
    if is_win:
        binaries += find_dll(dlls_dir, python_base, "_ctypes.pyd")
        binaries += find_dll(dlls_dir, python_base, "libffi-8.dll")
        binaries += find_dll(dlls_dir, python_base, "libffi-7.dll")

    datas, bins, hidden = collect_all("ctypes")
    return datas, bins + binaries, hidden

# -----------------------------------------------------------------------------
# Dependency Collection
# -----------------------------------------------------------------------------

ctypes_datas, ctypes_bins, ctypes_hidden = collect_ctypes_dependencies()

hiddenimports = (
    ctypes_hidden
    + [
        "_ctypes",
        "ctypes",
        "ctypes.util",
        "docx", 
        "pypdf",
        "win32timezone"
    ]
)

hiddenimports += collect_submodules("src")

pil_datas, pil_bins, pil_hidden = collect_all("PIL")
hiddenimports += pil_hidden

datas = [
] + ctypes_datas + pil_datas

binaries = ctypes_bins + pil_bins

# -----------------------------------------------------------------------------
# Analysis Layer
# -----------------------------------------------------------------------------

a = Analysis(
    [ENTRYPOINT],
    pathex=[ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'pandas', 'scipy', 
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 
        'IPython', 'jupyter', 'notebook', 'wx'    ],
    noarchive=False,
    optimize=2,
)

# -----------------------------------------------------------------------------
# PYZ / EXE / COLLECT Construction
# -----------------------------------------------------------------------------

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,              
    console=False,
    disable_windowed_traceback=False
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)