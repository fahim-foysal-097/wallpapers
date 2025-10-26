#!/usr/bin/env python3
"""
generate_json.py - generate indexed JSON for wallpapers & categories.

Scans:
  - wallpapers/         -> json/wallpapers.json
  - wallpapers-mobile/  -> json/wallpapers-mobile.json

Writes:
  - json/wallpapers.json
  - json/wallpapers-mobile.json
  - json/categories.json   (contains desktop/mobile category arrays)

Each wallpaper entry includes:
  { "filename","url","thumb_url","size","modified","category" }

Behavior:
 - GIFs are included in the index (so they appear in the gallery),
   but **thumb_url will not be provided for .gif** files (so the frontend will
   use the original image as requested).

Quiet operation. Produces JSON files and prints one machine-parseable summary line:
  JSON_SUMMARY: desktop=N mobile=M total=T time_ms=...
"""

from pathlib import Path
import json
from datetime import datetime, timezone
from typing import List, Dict, Tuple
import time

# Config: (src_dir, output_json, thumb_root)
ENTRIES = [
    (Path("wallpapers"), Path("json/wallpapers.json"), Path("thumbnail/wallpapers-thumb")),
    (Path("wallpapers-mobile"), Path("json/wallpapers-mobile.json"), Path("thumbnail/mobile-wallpapers-thumb")),
]

# Known image extensions (we index GIFs too; thumbnails for GIFs are not used)
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff", ".svg"}

CATEGORIES_OUT = Path("json/categories.json")


def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTS


def make_entry(rel_path: Path, src_root: Path, thumb_root: Path) -> dict:
    full_path = src_root.joinpath(rel_path)
    stat = full_path.stat()
    modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

    suffix = full_path.suffix.lower()
    thumb_url = None
    if suffix != ".gif":
        thumb_candidate = thumb_root.joinpath(rel_path.with_suffix(".webp"))
        if thumb_candidate.exists():
            thumb_url = str(thumb_candidate.as_posix())

    return {
        "filename": rel_path.name,
        "url": str(src_root.joinpath(rel_path).as_posix()),
        "thumb_url": thumb_url,
        "size": stat.st_size,
        "modified": modified,
        "category": rel_path.parent.name if rel_path.parent != Path(".") else "uncategorized"
    }


def generate_for(src_dir: Path, out_file: Path, thumb_dir: Path) -> Tuple[List[dict], Dict[str, int]]:
    if not src_dir.exists() or not src_dir.is_dir():
        return [], {}

    entries = []
    cat_counts = {}

    # files directly inside root
    files_root = sorted([x for x in src_dir.iterdir() if x.is_file() and is_image(x)], key=lambda p: p.name.lower())
    for p in files_root:
        rel = Path(p.name)
        ent = make_entry(rel, src_dir, thumb_dir)
        entries.append(ent)
        cat = ent["category"] or "uncategorized"
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    # subdirectories (categories)
    dirs = sorted([x for x in src_dir.iterdir() if x.is_dir()], key=lambda p: p.name.lower())
    for d in dirs:
        files = sorted([x for x in d.iterdir() if x.is_file() and is_image(x)], key=lambda p: p.name.lower())
        for f in files:
            rel = Path(d.name) / f.name
            ent = make_entry(rel, src_dir, thumb_dir)
            entries.append(ent)
            cat = ent["category"] or "uncategorized"
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

    # write JSON
    out_file.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(entries),
        "wallpapers": entries
    }
    with out_file.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)

    return entries, cat_counts


def main():
    t0 = time.perf_counter()

    categories_summary = {
        "desktop": [],
        "mobile": []
    }
    desktop_count = 0
    mobile_count = 0

    for src, out, thumb in ENTRIES:
        entries, counts = generate_for(src, out, thumb)
        total = sum(counts.values()) if counts else 0
        arr = []
        arr.append({"name": "all", "label": "All", "count": total})
        for k in sorted(counts.keys()):
            arr.append({"name": k, "label": k, "count": counts[k]})
        if src.name.startswith("wallpapers-mobile"):
            categories_summary["mobile"] = arr
            mobile_count = total
        else:
            categories_summary["desktop"] = arr
            desktop_count = total

    # write categories.json
    CATEGORIES_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CATEGORIES_OUT.open("w", encoding="utf-8") as fh:
        json.dump(categories_summary, fh, indent=2, ensure_ascii=False)

    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    total_count = desktop_count + mobile_count

    # machine-parseable single line
    print(f"JSON_SUMMARY: desktop={desktop_count} mobile={mobile_count} total={total_count} time_ms={elapsed_ms}")


if __name__ == "__main__":
    main()
