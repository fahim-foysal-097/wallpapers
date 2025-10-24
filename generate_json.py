#!/usr/bin/env python3
"""
generate_json.py

Scan both:
  - wallpapers/         -> json/wallpapers.json
  - wallpapers-mobile/  -> json/wallpapers-mobile.json

Creates json/ if needed. Outputs timezone-aware ISO timestamps.

Usage:
    python3 generate_json.py
"""

from pathlib import Path
import json
from datetime import datetime, timezone

# Config - change paths if you need different locations
ENTRIES = [
    (Path("wallpapers"), Path("json/wallpapers.json")),
    (Path("wallpapers-mobile"), Path("json/wallpapers-mobile.json")),
]

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff", ".svg"}

def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTS

def make_entry(path: Path, dir_path: Path) -> dict:
    stat = path.stat()
    modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
    return {
        "filename": path.name,
        "url": str(dir_path.joinpath(path.name).as_posix()),
        "size": stat.st_size,
        "modified": modified
    }

def generate_for(src_dir: Path, out_file: Path) -> int:
    if not src_dir.exists() or not src_dir.is_dir():
        print(f"Skipping: '{src_dir}' not found or not a directory.")
        return 0

    files = sorted([p for p in src_dir.iterdir() if p.is_file() and is_image(p)], key=lambda p: p.name.lower())
    entries = []
    for p in files:
        try:
            entries.append(make_entry(p, src_dir))
        except Exception as e:
            print(f"Warning: couldn't stat {p}: {e}")

    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(entries),
        "wallpapers": entries
    }

    out_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with out_file.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        print(f"Wrote {out_file} ({len(entries)} images).")
    except Exception as e:
        print(f"Error writing {out_file}: {e}")

    return len(entries)

def main():
    total = 0
    for src, out in ENTRIES:
        n = generate_for(src, out)
        total += n
    if total == 0:
        print("No images found in either directory (wallpapers/ and wallpapers-mobile/).")

if __name__ == "__main__":
    main()
