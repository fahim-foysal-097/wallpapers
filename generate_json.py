#!/usr/bin/env python3
"""
generate_json.py

Scan the `wallpapers/` directory for image files and generate `wallpapers.json`.
Place this script in your repo root and run `python3 generate_json.py`.

This version uses timezone-aware UTC datetimes to avoid DeprecationWarning.
"""

from pathlib import Path
import json
from datetime import datetime, timezone

# Config
WALLPAPER_DIR = Path("wallpapers")
OUTPUT_FILE = Path("json/wallpapers.json")
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff", ".svg"}

def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTS

def make_entry(path: Path) -> dict:
    stat = path.stat()
    # timezone-aware UTC ISO
    modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
    return {
        "filename": path.name,
        "url": str(WALLPAPER_DIR.joinpath(path.name).as_posix()),
        "size": stat.st_size,
        "modified": modified
    }

def main():
    if not WALLPAPER_DIR.exists() or not WALLPAPER_DIR.is_dir():
        print(f"Error: '{WALLPAPER_DIR}' not found. Create it and put images inside.")
        return

    files = sorted([p for p in WALLPAPER_DIR.iterdir() if p.is_file() and is_image(p)], key=lambda p: p.name.lower())
    entries = []
    for p in files:
        try:
            entries.append(make_entry(p))
        except Exception as e:
            print(f"Warning: couldn't stat {p}: {e}")

    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(entries),
        "wallpapers": entries
    }

    with OUTPUT_FILE.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)

    print(f"Wrote {OUTPUT_FILE} ({len(entries)} images).")

if __name__ == "__main__":
    main()
