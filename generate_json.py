#!/usr/bin/env python3
"""
generate_json.py

Scan the `wallpapers/` directory for image files and generate `wallpapers.json`.
Place this script in your repo root and run `python3 generate_json.py`.

Output:
- wallpapers.json : list of objects:
  { "filename": "name.jpg", "url": "wallpapers/name.jpg",
    "size": 123456, "modified": "2025-10-23T15:12:34" }
"""

import os
import json
from datetime import datetime

# Config
WALLPAPER_DIR = "wallpapers"   # relative to script location
OUTPUT_FILE = "wallpapers.json"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff", ".svg"}

def is_image(filename):
    _, ext = os.path.splitext(filename.lower())
    return ext in IMAGE_EXTS

def make_entry(root, filename):
    path = os.path.join(root, filename)
    stat = os.stat(path)
    modified = datetime.utcfromtimestamp(stat.st_mtime).isoformat() + "Z"
    return {
        "filename": filename,
        "url": os.path.join(WALLPAPER_DIR, filename).replace("\\", "/"),
        "size": stat.st_size,
        "modified": modified
    }

def main():
    if not os.path.isdir(WALLPAPER_DIR):
        print(f"Error: '{WALLPAPER_DIR}' not found. Create it and put images inside.")
        return

    files = [f for f in os.listdir(WALLPAPER_DIR) if os.path.isfile(os.path.join(WALLPAPER_DIR, f)) and is_image(f)]
    files.sort()  # alphabetical; you can change to sort by modified time if wanted

    entries = []
    for f in files:
        try:
            entries.append(make_entry(WALLPAPER_DIR, f))
        except Exception as e:
            print(f"Warning: couldn't stat {f}: {e}")

    data = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "count": len(entries),
        "wallpapers": entries
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)

    print(f"Wrote {OUTPUT_FILE} ({len(entries)} images).")

if __name__ == "__main__":
    main()
