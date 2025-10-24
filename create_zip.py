#!/usr/bin/env python3
"""
create_zip.py

Create ZIP archives:
  - wallpaper-all.zip        (contents of 'wallpapers/')
  - wallpaper-mobile-all.zip (contents of 'wallpapers-mobile/')

Files are stored with their path (e.g. wallpapers/xxx.jpg) so folder
structure is preserved. Existing output files are overwritten.

Usage:
    python3 create_zip.py
"""

from pathlib import Path
import zipfile
import sys

# Configuration
PAIRS = [
    (Path("wallpapers"), Path("wallpaper-all.zip")),
    (Path("wallpapers-mobile"), Path("wallpaper-mobile-all.zip")),
]

# Zip params
ZIP_COMPRESSION = zipfile.ZIP_DEFLATED
ZIP_COMPRESSLEVEL = 9

def create_zip(src_dir: Path, out_zip: Path):
    if not src_dir.exists() or not src_dir.is_dir():
        print(f"Skipping: '{src_dir}' not found or not a directory.")
        return

    # remove existing zip (try/except to avoid permission crashes)
    if out_zip.exists():
        try:
            out_zip.unlink()
        except Exception as e:
            print(f"Warning: couldn't remove existing {out_zip}: {e}")
            return

    print(f"Creating {out_zip} from {src_dir} ...")
    # write files
    try:
        # Python >= 3.7 supports compresslevel argument; fall back if not available
        try:
            zf = zipfile.ZipFile(out_zip, mode="w", compression=ZIP_COMPRESSION, compresslevel=ZIP_COMPRESSLEVEL)
        except TypeError:
            # older Python: no compresslevel parameter
            zf = zipfile.ZipFile(out_zip, mode="w", compression=ZIP_COMPRESSION)

        with zf:
            count = 0
            for p in sorted(src_dir.rglob("*")):
                if p.is_file():
                    # store with path relative to repo root (so zip contains wallpapers/xxx)
                    arcname = p.as_posix()
                    print(f"  Adding {arcname}")
                    zf.write(p, arcname)
                    count += 1

        print(f"Wrote {out_zip} ({out_zip.stat().st_size} bytes) - {count} files")

        # integrity check
        with zipfile.ZipFile(out_zip, mode="r") as zf_check:
            bad = zf_check.testzip()
            if bad is None:
                print("  ZIP integrity check: OK")
            else:
                print(f"  ZIP integrity check: BAD file: {bad}")

    except Exception as exc:
        print(f"Error creating {out_zip}: {exc}")

def main():
    any_created = False
    for src, out in PAIRS:
        create_zip(src, out)
        if out.exists():
            any_created = True

    if not any_created:
        print("No zip files created (source directories missing?).")
        sys.exit(1)

if __name__ == "__main__":
    main()
