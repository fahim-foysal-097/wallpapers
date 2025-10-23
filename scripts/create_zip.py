#!/usr/bin/env python3
"""
create_zip.py

Create a ZIP archive 'wallpaper-all.zip' containing the contents of the
'wallpapers/' directory (files only, preserves folder structure under wallpapers/).

Usage:
    python3 create_zip.py
"""

from pathlib import Path
import zipfile
import sys

# locate repo root relative to this script file
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

WALLPAPER_DIR = REPO_ROOT / "wallpapers"
OUTPUT_ZIP = REPO_ROOT / "wallpaper-all.zip"

def main():
    if not WALLPAPER_DIR.exists() or not WALLPAPER_DIR.is_dir():
        print(f"Error: '{WALLPAPER_DIR}' not found. Create it and put images inside.")
        sys.exit(1)

    # Remove existing output if you want fresh overwrite (optional)
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()

    # Create zip (overwrite if exists)
    with zipfile.ZipFile(OUTPUT_ZIP, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for p in sorted(WALLPAPER_DIR.rglob("*")):
            if p.is_file():
                # IMPORTANT: store path relative to repo root, NOT including '..' or absolute components
                arcname = p.relative_to(REPO_ROOT).as_posix()  # e.g. "wallpapers/subdir/file.jpg"
                print(f"Adding {p} as {arcname}")
                zf.write(p, arcname)

    print(f"Wrote {OUTPUT_ZIP} ({OUTPUT_ZIP.stat().st_size} bytes)")

    # quick integrity check
    with zipfile.ZipFile(OUTPUT_ZIP, mode="r") as zf:
        bad = zf.testzip()
        if bad is None:
            print("ZIP integrity check: OK")
        else:
            print(f"ZIP integrity check: BAD file: {bad}")

if __name__ == "__main__":
    main()
