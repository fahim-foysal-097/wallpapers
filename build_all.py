#!/usr/bin/env python3
"""
build_all.py

Full pipeline that runs:
  1) generate_thumbs.py
  2) generate_json.py
  3) writes json/badge.json
  4) generates json/badge.svg (static SVG badge that is embedded in README)

Usage:
    python3 build_all.py
"""

from pathlib import Path
import subprocess
import sys
import json
from datetime import datetime, timezone
import html

ROOT = Path(__file__).parent.resolve()
JSON_DIR = ROOT / "json"
BADGE_JSON = JSON_DIR / "badge.json"
BADGE_SVG = JSON_DIR / "badge.svg"

SCRIPTS = [
    ROOT / "generate_thumbs.py",
    ROOT / "generate_json.py",
]

def run_script(script: Path):
    if not script.exists():
        raise FileNotFoundError(f"Required script not found: {script}")
    print()
    print(f"-> Running {script.name} ...")
    res = subprocess.run([sys.executable, str(script)], cwd=str(ROOT))
    if res.returncode != 0:
        raise RuntimeError(f"Script {script.name} failed with exit code {res.returncode}")

def load_json_safe(path: Path):
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as e:
        print(f"Warning: failed to parse JSON {path}: {e}")
        return None

def compute_counts():
    desktop_path = JSON_DIR / "wallpapers.json"
    mobile_path = JSON_DIR / "wallpapers-mobile.json"

    desktop = load_json_safe(desktop_path)
    mobile = load_json_safe(mobile_path)

    desktop_count = 0
    mobile_count = 0

    if desktop:
        desktop_count = int(desktop.get("count") if isinstance(desktop.get("count"), int) else len(desktop.get("wallpapers", [])))
    else:
        print(f"Note: {desktop_path} missing or invalid -> desktop count = 0")

    if mobile:
        mobile_count = int(mobile.get("count") if isinstance(mobile.get("count"), int) else len(mobile.get("wallpapers", [])))
    else:
        print(f"Note: {mobile_path} missing or invalid -> mobile count = 0")

    total = desktop_count + mobile_count
    return desktop_count, mobile_count, total

def write_badge_json(desktop_count, mobile_count, total):
    JSON_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload = {
        "generated_at": generated_at,
        "desktop": desktop_count,
        "mobile": mobile_count,
        "total_wallpapers": total
    }
    with BADGE_JSON.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    print(f"Wrote badge JSON -> {BADGE_JSON} (total={total})")

# ---------- SVG badge generator ----------
# Simple badge renderer inspired by shields style (label + value)
def generate_badge_svg(label: str, value: str, color_hex: str = "#8A2BE2"):
    """
    Create a simple SVG badge with `label` (left) and `value` (right).
    Returns SVG string.
    """
    # Safe-escape label and value for XML
    label_esc = html.escape(str(label))
    value_esc = html.escape(str(value))

    # Basic metrics (approximate): per-char widths
    # This is simple and works well for short labels/values.
    char_w = 6.8  # approximate average char width in px for 11px Roboto-like font
    pad_x = 10    # horizontal padding on each side of text area
    height = 20
    left_font_size = 11
    right_font_size = 11

    left_width = max(40, int(len(label) * char_w) + pad_x * 2)
    right_width = max(40, int(len(value) * char_w) + pad_x * 2)
    total_width = left_width + right_width
    rx = 4  # corner radius

    left_bg = "#555"
    right_bg = color_hex

    left_text_x = left_width / 2
    right_text_x = left_width + right_width / 2
    text_y = (height / 2) + 4  # vertical alignment tweak

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{height}" role="img" aria-label="{label_esc}: {value_esc}">
  <title>{label_esc}: {value_esc}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#fff" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".05"/>
  </linearGradient>

  <!-- background -->
  <rect rx="{rx}" width="{total_width}" height="{height}" fill="{left_bg}"/>
  <rect rx="{rx}" x="{left_width}" width="{right_width}" height="{height}" fill="{right_bg}"/>

  <!-- overlay for subtle gloss -->
  <rect rx="{rx}" width="{total_width}" height="{height}" fill="url(#s)"/>

  <!-- divider -->
  <rect x="{left_width}" width="1" height="{height}" fill="#000" opacity="0.2"/>

  <!-- text -->
  <g fill="#fff" text-anchor="middle" font-family="Verdana,DejaVu Sans,Segoe UI,Arial,sans-serif" font-size="{left_font_size}">
    <text x="{left_text_x:.1f}" y="{text_y:.1f}" fill="#fff" fill-opacity="0.9">{label_esc}</text>
    <text x="{right_text_x:.1f}" y="{text_y:.1f}" fill="#fff" font-weight="700">{value_esc}</text>
  </g>
</svg>"""
    return svg

def write_badge_svg(total):
    # label left, value right
    label = "wallpapers"
    value = str(total)
    svg = generate_badge_svg(label, value, color_hex="#8A2BE2")
    JSON_DIR.mkdir(parents=True, exist_ok=True)
    with BADGE_SVG.open("w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"Wrote SVG badge -> {BADGE_SVG}")

def main():
    print("BUILD: starting full pipeline")
    # run each script in order - if one fails, stop
    for script in SCRIPTS:
        try:
            run_script(script)
        except Exception as e:
            print(f"ERROR: {e}")
            sys.exit(1)

    # compute counts and write badge json + svg
    dcount, mcount, total = compute_counts()
    write_badge_json(dcount, mcount, total)
    write_badge_svg(total)

    print()
    print("BUILD: done.")

if __name__ == "__main__":
    main()
