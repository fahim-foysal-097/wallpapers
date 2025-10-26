#!/usr/bin/env python3
"""
add_favorites.py

Append filenames to favorites.json without replacing existing entries.

Usage:
    # append file names via arguments
    python3 create_favorites.py beach.jpg sunset.png

    # or run without args to enter names interactively (comma or newline separated)
    python3 create_favorites.py

Behavior:
- favorites.json will have structure: { "favorites": ["file1.jpg","file2.png", ...] }
- If favorites.json doesn't exist it will be created.
- Existing entries will be preserved and duplicates avoided (case-sensitive).
"""

from pathlib import Path
import json
import sys

FAV_FILE = Path("json/favorites.json")

def load_existing():
    if not FAV_FILE.exists():
        return []
    try:
        data = json.loads(FAV_FILE.read_text(encoding="utf-8"))
        favs = data.get("favorites", []) if isinstance(data, dict) else []
        if not isinstance(favs, list):
            return []
        return favs
    except Exception as e:
        print(f"Warning: could not read {FAV_FILE}: {e}")
        return []

def save_favorites(favs):
    obj = {"favorites": favs}
    # write atomically
    tmp = FAV_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(FAV_FILE)
    print(f"Wrote {FAV_FILE} ({len(favs)} favorites).")

def parse_input_args(args):
    # flatten args and split commas
    items = []
    for a in args:
        parts = [p.strip() for p in a.split(",") if p.strip()]
        items.extend(parts)
    return items

def interactive_input():
    print("Enter filenames to add to favorites. Separate by commas or new lines. Empty line to finish.")
    lines = []
    try:
        while True:
            line = input("> ").strip()
            if line == "":
                break
            lines.append(line)
    except EOFError:
        pass
    # join lines and split by comma
    joined = ",".join(lines)
    return [p.strip() for p in joined.split(",") if p.strip()]

def main():
    if len(sys.argv) > 1:
        new_items = parse_input_args(sys.argv[1:])
    else:
        new_items = interactive_input()

    if not new_items:
        print("No filenames provided. Exiting.")
        return

    existing = load_existing()
    # keep case-sensitive uniqueness, preserve existing order then append new unique ones
    existing_set = set(existing)
    appended = 0
    for item in new_items:
        if item not in existing_set:
            existing.append(item)
            existing_set.add(item)
            appended += 1

    if appended:
        save_favorites(existing)
        print(f"Added {appended} new favorite(s).")
    else:
        print("No new favorites to add (all items already present).")

if __name__ == "__main__":
    main()
