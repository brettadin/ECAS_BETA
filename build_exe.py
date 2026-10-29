"""Build script to create a standalone Windows executable (.exe) for ECAS using PyInstaller.

Usage:
    .venv\\Scripts\\python build_exe.py           # Builds onedir bundle (recommended, fast launch)
    .venv\\Scripts\\python build_exe.py --onefile # Builds single-file ECAS.exe
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


def build(onefile: bool = False) -> int:
    root = Path(__file__).resolve().parent
    main_py = root / "main.py"
    data_dir = root / "data"

    if not main_py.is_file():
        print(f"Error: Could not find entry point at {main_py}")
        return 1

    pyinstaller_exe = root / ".venv" / "Scripts" / "pyinstaller.exe"
    cmd = [str(pyinstaller_exe) if pyinstaller_exe.is_file() else "pyinstaller"]

    cmd.extend([
        "--name", "ECAS",
        "--clean",
        "--noconfirm",
    ])

    if onefile:
        cmd.append("--onefile")
        print("--> Configuring single-file executable (dist/ECAS.exe)...")
    else:
        cmd.append("--onedir")
        print("--> Configuring folder distribution (dist/ECAS/ECAS.exe, recommended)...")

    # Include local reference and catalogue data
    if data_dir.is_dir():
        cmd.extend(["--add-data", f"{data_dir};data"])

    # Explicitly ensure Qt / PySide6 / pyqtgraph plugins and dependencies are bundled
    cmd.extend([
        "--hidden-import", "PySide6.QtCore",
        "--hidden-import", "PySide6.QtWidgets",
        "--hidden-import", "PySide6.QtGui",
        "--hidden-import", "pyqtgraph",
        "--hidden-import", "numpy",
        "--hidden-import", "sqlite3",
    ])

    cmd.append(str(main_py))

    print(f"--> Running PyInstaller: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=root)

    if result.returncode == 0:
        if onefile:
            exe_path = root / "dist" / "ECAS.exe"
            print(f"\n[SUCCESS] Standalone single-file executable built at: {exe_path}")
        else:
            exe_path = root / "dist" / "ECAS" / "ECAS.exe"
            print(f"\n[SUCCESS] Standalone executable package built at: {exe_path}")
            print(f"          The entire folder '{root / 'dist' / 'ECAS'}' can be zipped and run on any Windows PC.")
    else:
        print(f"\n[ERROR] PyInstaller build failed with exit code {result.returncode}")

    return result.returncode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build ECAS Windows executable")
    parser.add_argument("--onefile", action="store_true", help="Build a single-file executable instead of onedir")
    args = parser.parse_args()
    sys.exit(build(onefile=args.onefile))

