#!/usr/bin/env python3
"""
generate_thumbs.py - generate thumbnails preserving subfolder structure.

Writes thumbnails into:
  - thumbnail/wallpapers-thumb/<category>/*.webp
  - thumbnail/mobile-wallpapers-thumb/<category>/*.webp

Behavior:
 - Animated GIFs (.gif) are skipped (no thumbnails).
 - This script emits a lightweight progress indicator on a single line
   during processing, and a single summary line at the end:
     THUMBS_SUMMARY: created=... up_to_date=... skipped_gif=... failed=... total=... time_ms=...
"""

from pathlib import Path
from PIL import Image
import sys
import time

SRC_DESKTOP = Path("wallpapers")
SRC_MOBILE = Path("wallpapers-mobile")
OUT_ROOT = Path("thumbnail")
OUT_DESKTOP = OUT_ROOT / "wallpapers-thumb"
OUT_MOBILE = OUT_ROOT / "mobile-wallpapers-thumb"
OUT_DESKTOP_FULLSCREEN = OUT_ROOT / "wallpapers-fullscreen"
OUT_MOBILE_FULLSCREEN = OUT_ROOT / "mobile-wallpapers-fullscreen"


DESKTOP_MAX = (640, 360)
MOBILE_MAX = (540, 960)

# Raster extensions we WILL create thumbnails for (GIF intentionally excluded)
RASTER_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}

OUT_FORMAT = "WEBP"
OUT_QUALITY = 80
FULLSCREEN_QUALITY = 80


def should_process(src: Path, dst: Path) -> bool:
    """
    Return True if we should (re)create dst from src.
    """
    if not src.exists():
        return False
    if not dst.exists():
        return True
    try:
        return src.stat().st_mtime > dst.stat().st_mtime
    except Exception:
        return True


def make_thumb(src_path: Path, dst_path: Path, max_size):
    """
    Create a WEBP thumbnail for src_path at dst_path.
    Raises exception on failure.
    """
    with Image.open(src_path) as im:
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        im.thumbnail(max_size, Image.LANCZOS)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        im.save(str(dst_path), OUT_FORMAT, quality=OUT_QUALITY, method=6)


def make_fullscreen_webp(src_path: Path, dst_path: Path):
    """
    Create a full-resolution WEBP for src_path at dst_path.
    Raises exception on failure.
    """
    with Image.open(src_path) as im:
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        im.save(str(dst_path), OUT_FORMAT, quality=FULLSCREEN_QUALITY, method=6)


def print_progress(counters: dict):
    """
    Print a lightweight progress indicator on the current terminal line.
    """
    total = counters.get("grand_total", 0)
    processed = counters["total"]
    if total > 0:
        percent = (processed / total) * 100
        prefix = f"{percent:.1f}% ({processed}/{total})"
    else:
        prefix = f"{processed} processed"
        
    msg = (f"\r[Progress] {prefix} | Created: {counters['created']} | "
           f"Up-to-date: {counters['up_to_date']} | Skipped: {counters['skipped_gif']} | "
           f"Failed: {counters['failed']}")
    # Pad with spaces to ensure previous longer lines are overwritten
    sys.stderr.write(f"{msg: <100}")
    sys.stderr.flush()


def count_all_eligible_files(src_dir: Path) -> int:
    """
    Count how many files we will eventually process in src_dir and its subfolders.
    """
    cnt = 0
    if not src_dir.exists() or not src_dir.is_dir():
        return 0
    # top-level
    for p in src_dir.iterdir():
        if p.is_file() and (p.suffix.lower() == ".gif" or p.suffix.lower() in RASTER_EXTS):
            cnt += 1
    # subfolders
    for d in src_dir.iterdir():
        if d.is_dir():
            for p in d.iterdir():
                if p.is_file() and (p.suffix.lower() == ".gif" or p.suffix.lower() in RASTER_EXTS):
                    cnt += 1
    return cnt


def process_folder_recursive(src_dir: Path, out_dir: Path, out_fullscreen_dir: Path, max_size, counters: dict):
    """
    Process files in src_dir root and in one level of subfolders (categories).
    Updates counters dict with keys: total, created, up_to_date, skipped_gif, failed
    """
    if not src_dir.exists() or not src_dir.is_dir():
        return

    # top-level files
    for p in sorted(src_dir.iterdir()):
        if p.is_file():
            counters["total"] += 1
            sfx = p.suffix.lower()
            if sfx == ".gif":
                counters["skipped_gif"] += 1
                print_progress(counters)
                continue
            if sfx not in RASTER_EXTS:
                continue
            dst_name = p.with_suffix("." + OUT_FORMAT.lower()).name
            dst_path = out_dir / dst_name
            dst_fs_path = out_fullscreen_dir / dst_name
            try:
                processed_any = False
                if should_process(p, dst_path):
                    make_thumb(p, dst_path, max_size)
                    processed_any = True
                if should_process(p, dst_fs_path):
                    make_fullscreen_webp(p, dst_fs_path)
                    processed_any = True
                
                if processed_any:
                    counters["created"] += 1
                else:
                    counters["up_to_date"] += 1
            except Exception:
                counters["failed"] += 1
            print_progress(counters)

    # subfolders (categories)
    for d in sorted([x for x in src_dir.iterdir() if x.is_dir()]):
        for p in sorted([x for x in d.iterdir() if x.is_file()]):
            counters["total"] += 1
            sfx = p.suffix.lower()
            if sfx == ".gif":
                counters["skipped_gif"] += 1
                print_progress(counters)
                continue
            if sfx not in RASTER_EXTS:
                continue
            rel = Path(d.name) / p.name
            dst_rel = rel.with_suffix("." + OUT_FORMAT.lower())
            dst_path = out_dir / dst_rel
            dst_fs_path = out_fullscreen_dir / dst_rel
            try:
                processed_any = False
                if should_process(p, dst_path):
                    make_thumb(p, dst_path, max_size)
                    processed_any = True
                if should_process(p, dst_fs_path):
                    make_fullscreen_webp(p, dst_fs_path)
                    processed_any = True
                
                if processed_any:
                    counters["created"] += 1
                else:
                    counters["up_to_date"] += 1
            except Exception:
                counters["failed"] += 1
            print_progress(counters)


def count_existing_thumbs(root: Path) -> int:
    if not root.exists():
        return 0
    total = 0
    for p in root.rglob("*.webp"):
        if p.is_file():
            total += 1
    return total


def main():
    t0 = time.perf_counter()

    grand_total = count_all_eligible_files(SRC_DESKTOP) + count_all_eligible_files(SRC_MOBILE)

    counters = {
        "grand_total": grand_total,
        "total": 0,
        "created": 0,
        "up_to_date": 0,
        "skipped_gif": 0,
        "failed": 0,
    }

    existing_before = count_existing_thumbs(OUT_ROOT)

    # run processors (quiet)
    process_folder_recursive(SRC_DESKTOP, OUT_DESKTOP, OUT_DESKTOP_FULLSCREEN, DESKTOP_MAX, counters)
    process_folder_recursive(SRC_MOBILE, OUT_MOBILE, OUT_MOBILE_FULLSCREEN, MOBILE_MAX, counters)

    existing_after = count_existing_thumbs(OUT_ROOT)
    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    sys.stderr.write("\n") # End the progress indicator line
    sys.stderr.flush()

    # Human-friendly short line
    created = counters["created"]
    up_to_date = counters["up_to_date"]
    skipped = counters["skipped_gif"]
    failed = counters["failed"]
    total = counters["total"]
    delta = existing_after - existing_before

    print(f"Created {created} thumbnails (skipped {skipped} GIFs, {up_to_date} up-to-date, {failed} failed).")
    # machine-parseable summary (one line)
    print(
        f"THUMBS_SUMMARY: created={created} up_to_date={up_to_date} skipped_gif={skipped} failed={failed} "
        f"total_processed={total} existing_before={existing_before} existing_after={existing_after} added={delta} time_ms={elapsed_ms}"
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
