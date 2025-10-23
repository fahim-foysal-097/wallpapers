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

WALLPAPER_DIR = Path("wallpapers")
OUTPUT_ZIP = Path("wallpaper-all.zip")

def main():
    if not WALLPAPER_DIR.exists() or not WALLPAPER_DIR.is_dir():
        print(f"Error: '{WALLPAPER_DIR}' not found. Create it and put images inside.")
        sys.exit(1)

    # Create zip (overwrite if exists)
    with zipfile.ZipFile(OUTPUT_ZIP, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for p in sorted(WALLPAPER_DIR.rglob("*")):
            if p.is_file():
                # store with path relative to repo root so zip contains wallpapers/<name>
                arcname = p.as_posix()
                print(f"Adding {arcname}")
                zf.write(p, arcname)
    print(f"Wrote {OUTPUT_ZIP} ({OUTPUT_ZIP.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
