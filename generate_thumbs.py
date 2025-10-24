#!/usr/bin/env python3
"""
generate_thumbs.py

Generate thumbnails for wallpapers/ and wallpapers-mobile/ into thumbnail/:

  - thumbnail/wallpapers-thumb/
  - thumbnail/mobile-wallpapers-thumb/

This script requires Pillow:
    pip install pillow

Usage:
    python3 generate_thumbs.py
"""

from pathlib import Path
from PIL import Image
import sys

# CONFIG
SRC_DESKTOP = Path("wallpapers")
SRC_MOBILE = Path("wallpapers-mobile")
OUT_ROOT = Path("thumbnails")
OUT_DESKTOP = OUT_ROOT / "wallpapers-thumb"
OUT_MOBILE = OUT_ROOT / "mobile-wallpapers-thumb"

# bounding box for thumbnails (max width, max height)
DESKTOP_MAX = (640, 360)    # ~16:9 thumbs, 
MOBILE_MAX = (540, 960)     # portrait-ish thumb for mobile gallery

# allowed raster extensions
RASTER_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".gif"}

# output format and options
OUT_FORMAT = "WEBP"  # use WEBP for smaller filesize; change to "JPEG" for .jpg output
OUT_QUALITY = 85

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def should_process(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    if not dst.exists():
        return True
    try:
        return src.stat().st_mtime > dst.stat().st_mtime
    except Exception:
        return True

def make_thumb(src_path: Path, dst_path: Path, max_size):
    try:
        with Image.open(src_path) as im:
            # convert to RGB for consistent output (skip alpha for webp/jpg)
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            im.thumbnail(max_size, Image.LANCZOS)
            # ensure parent exists
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            # use WEBP extension
            dst_path_str = str(dst_path)
            im.save(dst_path_str, OUT_FORMAT, quality=OUT_QUALITY, method=6)
            print(f"Thumbnail: {dst_path} ({im.size[0]}x{im.size[1]})")
    except Exception as e:
        print(f"Failed to create thumb for {src_path}: {e}")

def process_folder(src_dir: Path, out_dir: Path, max_size):
    if not src_dir.exists() or not src_dir.is_dir():
        print(f"Source not found: {src_dir} — skipping")
        return 0
    ensure_dir(out_dir)
    count = 0
    for p in sorted(src_dir.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() not in RASTER_EXTS:
            # skip SVG and other non-raster
            print(f"Skipping non-raster: {p.name}")
            continue
        dst_name = p.with_suffix("." + OUT_FORMAT.lower()).name
        dst_path = out_dir / dst_name
        if should_process(p, dst_path):
            make_thumb(p, dst_path, max_size)
        else:
            print(f"Up-to-date: {dst_path.name}")
        count += 1
    return count

def main():
    total = 0
    total += process_folder(SRC_DESKTOP, OUT_DESKTOP, DESKTOP_MAX)
    total += process_folder(SRC_MOBILE, OUT_MOBILE, MOBILE_MAX)
    print(f"Done. Processed {total} images.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
