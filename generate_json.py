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
"""

from pathlib import Path
import json
from datetime import datetime, timezone
from typing import List, Dict, Tuple

# Config: (src_dir, output_json, thumb_root)
ENTRIES = [
    (Path("wallpapers"), Path("json/wallpapers.json"), Path("thumbnail/wallpapers-thumb")),
    (Path("wallpapers-mobile"), Path("json/wallpapers-mobile.json"), Path("thumbnail/mobile-wallpapers-thumb")),
]

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff", ".svg"}

CATEGORIES_OUT = Path("json/categories.json")


def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTS


def thumb_name_from(src_name: str) -> str:
    base = Path(src_name).stem
    return base + ".webp"


def make_entry(rel_path: Path, src_root: Path, thumb_root: Path) -> dict:
    # rel_path is relative path under src_root (e.g. 'blue/sky.jpg' or 'sunset.jpg')
    full_path = src_root.joinpath(rel_path)
    stat = full_path.stat()
    modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
    # compute thumb candidate path inside thumb_root, preserving relative folder structure
    thumb_candidate = thumb_root.joinpath(rel_path.with_suffix(".webp"))
    thumb_url = None
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
    """
    Returns list of entries and a per-category count dict
    """
    if not src_dir.exists() or not src_dir.is_dir():
        print(f"Skipping: '{src_dir}' not found or not a directory.")
        return [], {}

    entries: List[dict] = []
    cat_counts: Dict[str, int] = {}
    # files directly inside root
    for p in sorted([x for x in src_dir.iterdir() if x.is_file() and is_image(x)], key=lambda p: p.name.lower()):
        rel = Path(p.name)
        ent = make_entry(rel, src_dir, thumb_dir)
        entries.append(ent)
        cat = ent["category"] or "uncategorized"
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    # subdirectories (categories)
    for d in sorted([x for x in src_dir.iterdir() if x.is_dir()], key=lambda p: p.name.lower()):
        for f in sorted([x for x in d.iterdir() if x.is_file() and is_image(x)], key=lambda p: p.name.lower()):
            rel = Path(d.name) / f.name
            ent = make_entry(rel, src_dir, thumb_dir)
            entries.append(ent)
            cat = ent["category"] or "uncategorized"
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

    # write JSON
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(entries),
        "wallpapers": entries
    }
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    print(f"Wrote {out_file} ({len(entries)} images).")
    return entries, cat_counts


def main():
    categories_summary = {
        "desktop": [],
        "mobile": []
    }
    for src, out, thumb in ENTRIES:
        entries, counts = generate_for(src, out, thumb)
        # map counts into array sorted
        arr = []
        total = sum(counts.values()) if counts else 0
        arr.append({"name": "all", "label": "All", "count": total})
        for k in sorted(counts.keys()):
            arr.append({"name": k, "label": k, "count": counts[k]})
        if src.name.startswith("wallpapers-mobile"):
            categories_summary["mobile"] = arr
        else:
            categories_summary["desktop"] = arr

    # write categories.json
    CATEGORIES_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CATEGORIES_OUT.open("w", encoding="utf-8") as fh:
        json.dump(categories_summary, fh, indent=2, ensure_ascii=False)
    print(f"Wrote categories JSON -> {CATEGORIES_OUT}")


if __name__ == "__main__":
    main()
