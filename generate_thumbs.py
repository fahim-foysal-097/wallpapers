#!/usr/bin/env python3
"""
generate_thumbs.py - generate thumbnails preserving subfolder structure.

Writes thumbnails into:
  - thumbnail/wallpapers-thumb/<category>/*.webp
  - thumbnail/mobile-wallpapers-thumb/<category>/*.webp
"""

from pathlib import Path
from PIL import Image
import sys

SRC_DESKTOP = Path("wallpapers")
SRC_MOBILE = Path("wallpapers-mobile")
OUT_ROOT = Path("thumbnail")
OUT_DESKTOP = OUT_ROOT / "wallpapers-thumb"
OUT_MOBILE = OUT_ROOT / "mobile-wallpapers-thumb"

DESKTOP_MAX = (640, 360)
MOBILE_MAX = (540, 960)

RASTER_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".gif"}

OUT_FORMAT = "WEBP"
OUT_QUALITY = 90

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
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            im.thumbnail(max_size, Image.LANCZOS)
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            dst_path_str = str(dst_path)
            im.save(dst_path_str, OUT_FORMAT, quality=OUT_QUALITY, method=6)
            print(f"Thumbnail: {dst_path} ({im.size[0]}x{im.size[1]})")
    except Exception as e:
        print(f"Failed to create thumb for {src_path}: {e}")

def process_folder_recursive(src_dir: Path, out_dir: Path, max_size):
    if not src_dir.exists() or not src_dir.is_dir():
        print(f"Source not found: {src_dir} — skipping")
        return 0
    count = 0
    # top-level files
    for p in sorted(src_dir.iterdir()):
        if p.is_file() and p.suffix.lower() in RASTER_EXTS:
            dst_name = p.with_suffix("." + OUT_FORMAT.lower()).name
            dst_path = out_dir / dst_name
            if should_process(p, dst_path):
                make_thumb(p, dst_path, max_size)
            else:
                print(f"Up-to-date: {dst_path.name}")
            count += 1
    # subfolders (categories) -> preserve path
    for d in sorted([x for x in src_dir.iterdir() if x.is_dir()]):
        for p in sorted([x for x in d.iterdir() if x.is_file() and x.suffix.lower() in RASTER_EXTS]):
            rel = Path(d.name) / p.name
            dst_rel = rel.with_suffix("." + OUT_FORMAT.lower())
            dst_path = out_dir / dst_rel
            if should_process(p, dst_path):
                make_thumb(p, dst_path, max_size)
            else:
                print(f"Up-to-date: {dst_path}")
            count += 1
    return count

def main():
    total = 0
    total += process_folder_recursive(SRC_DESKTOP, OUT_DESKTOP, DESKTOP_MAX)
    total += process_folder_recursive(SRC_MOBILE, OUT_MOBILE, MOBILE_MAX)
    print(f"Done. Processed {total} images.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
