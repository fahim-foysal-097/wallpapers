#!/usr/bin/env python3
"""
build_all.py - run full pipeline:
  optionally clean outputs -> generate_thumbs.py -> generate_json.py -> write badges

Usage:
  python build_all.py           # normal run
  python build_all.py --clean   # remove thumbnail/ and listed json files before running
"""
from pathlib import Path
import subprocess
import sys
import json
from datetime import datetime, timezone
import html
import shutil
import argparse
import time
import re
import os
import unicodedata

# Try to enable color support on Windows if colorama is present.
try:
    import colorama

    colorama.init()
except Exception:
    colorama = None  # not required; ANSI will still work on most Unix terminals

ROOT = Path(__file__).parent.resolve()
JSON_DIR = ROOT / "json"
BADGE_JSON = JSON_DIR / "badge.json"
BADGE_SVG = JSON_DIR / "badge.svg"

SCRIPTS = [
    ROOT / "generate_thumbs.py",
    ROOT / "generate_json.py",
]

# Files to remove inside json/ during cleanup
JSON_FILES_TO_REMOVE = [
    BADGE_JSON,
    BADGE_SVG,
    JSON_DIR / "wallpapers.json",
    JSON_DIR / "wallpapers-mobile.json",
    JSON_DIR / "categories.json",
]

THUMBNAIL_DIR = ROOT / "thumbnail"

# -------- ANSI helpers --------
CSI = "\033["
RESET = CSI + "0m"


def color_text(s: str, code: str) -> str:
    return f"{CSI}{code}m{s}{RESET}"


def bold(s: str) -> str:
    return color_text(s, "1")


def green(s: str) -> str:
    return color_text(s, "32")


def yellow(s: str) -> str:
    return color_text(s, "33")


def red(s: str) -> str:
    return color_text(s, "31")


def cyan(s: str) -> str:
    return color_text(s, "36")


def faint(s: str) -> str:
    return color_text(s, "2")


def magenta(s: str) -> str:
    return color_text(s, "35")


def blue(s: str) -> str:
    return color_text(s, "34")


def supports_ansi() -> bool:
    # Basic heuristic: on Windows, if colorama isn't available, disable ANSI
    if os.name == "nt" and colorama is None:
        return False
    return True


# If no ANSI support, make helpers no-op
if not supports_ansi():
    def color_text(s: str, code: str) -> str:
        return s

    def bold(s: str) -> str:
        return s

    def green(s: str) -> str:
        return s

    def yellow(s: str) -> str:
        return s

    def red(s: str) -> str:
        return s

    def cyan(s: str) -> str:
        return s

    def faint(s: str) -> str:
        return s

    def magenta(s: str) -> str:
        return s

    def blue(s: str) -> str:
        return s


# -------- utilities --------
def human_ms(ms: int) -> str:
    if ms < 1000:
        return f"{ms} ms"
    s = ms / 1000.0
    if s < 60:
        return f"{s:.2f} s"
    m = int(s // 60)
    sec = s - (m * 60)
    if sec < 1:
        return f"{m}m"
    return f"{m}m {sec:.0f}s"


def run_script_capture(script: Path):
    """
    Run a script and return CompletedProcess (with stdout/stderr captured).
    """
    if not script.exists():
        raise FileNotFoundError(f"Required script not found: {script}")
    # capture output for parsing, keep execution quiet
    proc = subprocess.run([sys.executable, str(script)], cwd=str(ROOT), capture_output=True, text=True)
    return proc


def load_json_safe(path: Path):
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as e:
        print(f"{yellow('Warning:')} failed to parse JSON {path}: {e}")
        return None


def compute_counts():
    desktop_path = JSON_DIR / "wallpapers.json"
    mobile_path = JSON_DIR / "wallpapers-mobile.json"

    desktop = load_json_safe(desktop_path)
    mobile = load_json_safe(mobile_path)

    desktop_count = 0
    mobile_count = 0

    if desktop:
        desktop_count = int(
            desktop.get("count")
            if isinstance(desktop.get("count"), int)
            else len(desktop.get("wallpapers", []))
        )

    if mobile:
        mobile_count = int(
            mobile.get("count")
            if isinstance(mobile.get("count"), int)
            else len(mobile.get("wallpapers", []))
        )

    total = desktop_count + mobile_count
    return desktop_count, mobile_count, total


def write_badge_json(desktop_count, mobile_count, total):
    JSON_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload = {
        "generated_at": generated_at,
        "desktop": desktop_count,
        "mobile": mobile_count,
        "total_wallpapers": total,
    }
    with BADGE_JSON.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)


def generate_badge_svg(label: str, value: str, color_hex: str = "#8A2BE2"):
    label_esc = html.escape(str(label))
    value_esc = html.escape(str(value))
    char_w = 6.8
    pad_x = 10
    height = 20
    left_font_size = 11
    right_font_size = 11
    left_width = max(40, int(len(label) * char_w) + pad_x * 2)
    right_width = max(40, int(len(value) * char_w) + pad_x * 2)
    total_width = left_width + right_width
    rx = 4
    left_bg = "#555"
    right_bg = color_hex
    left_text_x = left_width / 2
    right_text_x = left_width + right_width / 2
    text_y = (height / 2) + 4
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{height}" role="img" aria-label="{label_esc}: {value_esc}">
  <title>{label_esc}: {value_esc}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#fff" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".05"/>
  </linearGradient>
  <rect rx="{rx}" width="{total_width}" height="{height}" fill="{left_bg}"/>
  <rect rx="{rx}" x="{left_width}" width="{right_width}" height="{height}" fill="{right_bg}"/>
  <rect rx="{rx}" width="{total_width}" height="{height}" fill="url(#s)"/>
  <rect x="{left_width}" width="1" height="{height}" fill="#000" opacity="0.2"/>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,DejaVu Sans,Segoe UI,Arial,sans-serif" font-size="{left_font_size}">
    <text x="{left_text_x:.1f}" y="{text_y:.1f}" fill="#fff" fill-opacity="0.9">{label_esc}</text>
    <text x="{right_text_x:.1f}" y="{text_y:.1f}" fill="#fff" font-weight="700">{value_esc}</text>
  </g>
</svg>"""
    return svg


def write_badge_svg(total):
    label = "wallpapers"
    value = str(total)
    svg = generate_badge_svg(label, value, color_hex="#8A2BE2")
    JSON_DIR.mkdir(parents=True, exist_ok=True)
    with BADGE_SVG.open("w", encoding="utf-8") as fh:
        fh.write(svg)


# ---------- cleaning ----------
def clean_outputs():
    """
    Remove thumbnail directory (recursively) and specified JSON files inside json/.
    Returns dict describing what happened.
    """
    removed = {"thumbnail_removed": False, "files_removed": []}

    if THUMBNAIL_DIR.exists():
        if THUMBNAIL_DIR.is_dir():
            shutil.rmtree(THUMBNAIL_DIR)
            removed["thumbnail_removed"] = True
        else:
            THUMBNAIL_DIR.unlink()
            removed["thumbnail_removed"] = True

    for p in JSON_FILES_TO_REMOVE:
        if p.exists():
            p.unlink()
            removed["files_removed"].append(str(p))
    return removed


def count_thumbs(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for _ in root.rglob("*.webp") if _.is_file())


# ---------- parse summary lines from child scripts ----------
def parse_summary_line(stdout: str, marker: str) -> dict:
    """
    Parse a 'KEY=VALUE' style marker line from stdout.
    e.g. "THUMBS_SUMMARY: created=3 up_to_date=4 ... time_ms=123"
    """
    out = {}
    if not stdout:
        return out
    for line in stdout.splitlines():
        if marker in line:
            after = line.split(marker, 1)[1].strip()
            parts = after.split()
            for p in parts:
                if "=" not in p:
                    continue
                k, v = p.split("=", 1)
                try:
                    out[k] = int(v)
                except Exception:
                    out[k] = v
            break
    return out


# ---------- ANSI strip + display width ----------
_ansi_re = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(s: str) -> str:
    return _ansi_re.sub("", s)


def display_width(s: str) -> int:
    """
    Compute the terminal display width (columns) of a string by:
      - stripping ANSI escapes
      - summing widths of codepoints (wide characters count as 2)
    This handles most emoji and east-asian wide characters reasonably.
    """
    s = strip_ansi(s)
    w = 0
    for ch in s:
        ea = unicodedata.east_asian_width(ch)
        # F = Fullwidth, W = Wide (count as 2)
        if ea in ("F", "W"):
            w += 2
        else:
            w += 1
    return w


# ---------- formatted box printing (improved) ----------
def boxed_print(title: str, lines: list):
    """
    Print a box with a title and lines (each line is a string).
    Title may contain ANSI color codes and emoji; widths are calculated
    on the visible characters so borders align correctly.
    Improved with double-line borders for better visual appeal.
    """
    safe_lines = [str(x) for x in lines if x]  # filter empty lines
    # compute display widths (strip ansi and account for wide chars)
    title_disp_w = display_width(title)
    lines_disp_w = [display_width(l) for l in safe_lines]
    maxw = max(title_disp_w, *(lines_disp_w or [0]))
    # inner width is maxw (we'll add two space padding on each side)
    inner = maxw + 4
    horiz = "═" * inner

    # top
    print()
    print(cyan("╔" + horiz + "╗"))
    # title row: center according to display width
    title_pad_left = (inner - title_disp_w) // 2
    title_pad_right = inner - title_disp_w - title_pad_left
    title_str = "  " + (" " * (title_pad_left - 2)) + title + (" " * title_pad_right)
    print(cyan("║") + title_str + cyan("║"))
    # separator
    print(cyan("╟" + "─" * inner + "╢"))
    # content rows
    for ln, d_w in zip(safe_lines, lines_disp_w):
        pad_left = 2
        pad_right = inner - d_w - pad_left
        row = (" " * pad_left) + ln + (" " * pad_right)
        print(cyan("║") + row + cyan("║"))
    # bottom
    print(cyan("╚" + horiz + "╝"))
    print()


# ---------- main ----------
def main(argv=None):
    parser = argparse.ArgumentParser(description="Run wallpaper build pipeline.")
    parser.add_argument("--clean", action="store_true", help="Delete thumbnail/ and listed json files before running.")
    args = parser.parse_args(argv)

    overall_t0 = time.perf_counter()

    header = f"Wallpaper Build Pipeline — {datetime.now().astimezone().isoformat()}"
    print(bold(magenta(header)))

    if args.clean:
        removed = clean_outputs()
        clean_title = red("CLEAN")
        clean_lines = [
            f"Thumbnail directory removed: {green(str(removed['thumbnail_removed']))}",
            "JSON files removed:",
            *[f"  • {f}" for f in removed["files_removed"]],
        ]
        boxed_print(clean_title, clean_lines)

    # snapshot thumbnails before
    thumbs_before = count_thumbs(THUMBNAIL_DIR)

    # run scripts
    summaries = {}
    script_times = {}
    for script in SCRIPTS:
        name = script.name
        print(f"{blue('🡒')} Running {bold(name)} ...", flush=True)
        t0 = time.perf_counter()
        proc = run_script_capture(script)
        dt_ms = int((time.perf_counter() - t0) * 1000)
        script_times[name] = dt_ms

        if proc.returncode != 0:
            error_lines = [
                f"{name} failed with exit code {proc.returncode}",
            ]
            if proc.stdout:
                error_lines.append("STDOUT:")
                error_lines.extend([f"  {line}" for line in proc.stdout.strip().splitlines()])
            if proc.stderr:
                error_lines.append("STDERR:")
                error_lines.extend([f"  {line}" for line in proc.stderr.strip().splitlines()])
            boxed_print(red(f"✖ ERROR in {name}"), error_lines)
            sys.exit(proc.returncode)

        # parse markers
        if name == "generate_thumbs.py":
            summaries["thumbs"] = parse_summary_line(proc.stdout, "THUMBS_SUMMARY:")
            # also capture human-readable create line if present
            if proc.stdout:
                m = re.search(r"Created\s+(\d+)\s+thumbnails", proc.stdout)
                if m and "thumbs_human" not in summaries:
                    summaries["thumbs_human"] = m.group(0)
        elif name == "generate_json.py":
            summaries["json"] = parse_summary_line(proc.stdout, "JSON_SUMMARY:")

    # recompute thumbnail counts after
    thumbs_after = count_thumbs(THUMBNAIL_DIR)
    total_time_ms = int((time.perf_counter() - overall_t0) * 1000)

    # compute JSON counts
    dcount, mcount, total_count = compute_counts()

    # Build summary lines with colors and icons
    lines = [
        green("🖼 Thumbnails:"),
        f"  Before: {thumbs_before} | After: {thumbs_after} | Added: {green(str(thumbs_after - thumbs_before))}",
    ]
    if "thumbs" in summaries and summaries["thumbs"]:
        ts = summaries["thumbs"]
        created = ts.get("created", 0)
        up_to_date = ts.get("up_to_date", 0)
        skipped_gif = ts.get("skipped_gif", 0)
        failed = ts.get("failed", 0)
        time_ms = ts.get("time_ms", script_times.get("generate_thumbs.py", 0))
        lines.append(f"  Created: {green(str(created))} | Up-to-date: {yellow(str(up_to_date))} | Skipped GIF: {faint(str(skipped_gif))} | Failed: {red(str(failed))}")
        lines.append(f"  Time: {human_ms(time_ms)}")
    else:
        lines.append(f"  Time: {human_ms(script_times.get('generate_thumbs.py', 0))}")

    lines.append("")
    lines.append(green("JSON Files:"))
    if "json" in summaries and summaries["json"]:
        js = summaries["json"]
        jd = js.get("desktop", dcount)
        jm = js.get("mobile", mcount)
        jt = js.get("total", total_count)
        jtime = js.get("time_ms", script_times.get("generate_json.py", 0))
        lines.append(f"  Desktop: {green(str(jd))} | Mobile: {green(str(jm))} | Total: {bold(green(str(jt)))}")
        lines.append(f"  Time: {human_ms(jtime)}")
    else:
        lines.append(f"  Desktop: {green(str(dcount))} | Mobile: {green(str(mcount))} | Total: {bold(green(str(total_count)))}")
        lines.append(f"  Time: {human_ms(script_times.get('generate_json.py', 0))}")

    lines.append("")
    lines.append(green("𝒊 Badges:"))
    lines.append(f"  badge.json and badge.svg written | Total Wallpapers: {bold(str(total_count))}")

    lines.append("")
    lines.append(green("Timings:"))
    for n, ms in script_times.items():
        lines.append(f"  • {n}: {human_ms(ms)}")
    lines.append(f"  • Total build time: {bold(human_ms(total_time_ms))}")

    # nice success box
    boxed_print(green("BUILD SUCCESS ✔"), lines)

    # final one-line GO/NO-GO for CI readability
    print(green(f"✔ Build succeeded - total_wallpapers={total_count} thumbnails_added={thumbs_after - thumbs_before} time={human_ms(total_time_ms)}"))

    # write badges (perform after summarizing)
    write_badge_json(dcount, mcount, total_count)
    write_badge_svg(total_count)


if __name__ == "__main__":
    main()
