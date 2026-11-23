"""Fuse channel picks from several interpreters into heat maps and majority labels.

Usage:
    python fuse_picks.py PICKS SECTIONS_DIR OUT_DIR [--level "PhD student"] [--exclude ORG,S05]

PICKS is either the Google Sheet downloaded as CSV (File > Download > Comma-separated values)
or the JSON file from the Results tab ("Download all picks").
SECTIONS_DIR is the folder with the section images the interpreters saw.

For each interpreter and section only the latest save counts. An interpreter counts for a
section if they drew at least one shape or ticked "No channel". Picks made on an image of a
different size than the one in SECTIONS_DIR are left out with a warning.

Writes, per section:
    <name>_heatmap.npy   fraction of interpreters who picked each pixel (0 to 1)
    <name>_heatmap.png   the same as a grey image (0 = nobody, 255 = everybody)
    <name>_label.png     majority label (white where at least half picked)
and two tables:
    agreement.csv        interpreters per section and mean pairwise Dice
    interpreters.csv     code, experience and sections done per interpreter

Note: shapes are filled here with PIL. For self-crossing shapes this can differ by a few
pixels from the preview on the website, so use this script for numbers in the paper.
"""
import argparse
import csv
import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def load_rows(path):
    path = Path(path)
    if path.suffix.lower() == ".json":
        rows = json.loads(path.read_text(encoding="utf-8"))["rows"]
    else:
        with path.open(newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        polys = r["polygons"]
        if isinstance(polys, str):
            polys = json.loads(polys or "[]")
        none = r["no_channel"]
        if isinstance(none, str):
            none = none.strip().upper() == "TRUE"
        out.append({
            "code": str(r["code"]).strip().upper(),
            "level": r.get("level", ""),
            "section": r["section"],
            "width": int(float(r["width"])),
            "height": int(float(r["height"])),
            "no_channel": bool(none),
            "polygons": polys,
        })
    return out


def latest(rows):
    """Latest save per (code, section). Rows are in the order they were saved."""
    picks, level = {}, {}
    for r in rows:
        picks.setdefault(r["code"], {})[r["section"]] = r
        level[r["code"]] = r["level"]
    return picks, level


def mask(entry):
    m = Image.new("L", (entry["width"], entry["height"]), 0)
    draw = ImageDraw.Draw(m)
    for poly in entry["polygons"]:
        if len(poly) >= 3:
            draw.polygon([tuple(p) for p in poly], fill=1)
    return np.array(m, dtype=bool)


def dice(a, b):
    s = a.sum() + b.sum()
    return 1.0 if s == 0 else 2 * (a & b).sum() / s


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("picks")
    ap.add_argument("sections_dir")
    ap.add_argument("out_dir")
    ap.add_argument("--level", help="only use interpreters with this experience level")
    ap.add_argument("--exclude", default="", help="comma-separated codes to leave out")
    a = ap.parse_args()

    src, dst = Path(a.sections_dir), Path(a.out_dir)
    dst.mkdir(parents=True, exist_ok=True)
    picks, level = latest(load_rows(a.picks))
    skip = {c.strip().upper() for c in a.exclude.split(",") if c.strip()}
    codes = sorted(c for c in picks if c not in skip and (not a.level or level[c] == a.level))
    print(f"{len(codes)} interpreters:", ", ".join(f"{c} ({level[c]})" for c in codes))

    names = sorted({n for c in codes for n in picks[c]})
    agreement = [["section", "n_interpreters", "n_no_channel", "mean_pairwise_dice"]]
    for name in names:
        img = src / name
        if not img.exists():
            print(f"warning: {name} is not in {src}, skipped", file=sys.stderr)
            continue
        w, h = Image.open(img).size
        masks, n_none = [], 0
        for c in codes:
            e = picks[c].get(name)
            if not e or not (e["polygons"] or e["no_channel"]):
                continue
            if (e["width"], e["height"]) != (w, h):
                print(f"warning: {c} picked {name} at {e['width']}x{e['height']}, image is {w}x{h}; left out",
                      file=sys.stderr)
                continue
            n_none += not e["polygons"]
            masks.append(mask(e))
        if not masks:
            continue
        heat = np.mean(masks, axis=0)
        stem = Path(name).stem
        np.save(dst / f"{stem}_heatmap.npy", heat)
        Image.fromarray(np.round(heat * 255).astype(np.uint8)).save(dst / f"{stem}_heatmap.png")
        Image.fromarray((heat >= 0.5).astype(np.uint8) * 255).save(dst / f"{stem}_label.png")
        d = [dice(x, y) for x, y in combinations(masks, 2)]
        agreement.append([name, len(masks), n_none, f"{np.mean(d):.3f}" if d else ""])

    with (dst / "agreement.csv").open("w", newline="") as f:
        csv.writer(f).writerows(agreement)
    with (dst / "interpreters.csv").open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["code", "level", "sections_done"])
        for c in codes:
            wr.writerow([c, level[c], sum(bool(e["polygons"] or e["no_channel"]) for e in picks[c].values())])
    for row in agreement:
        print(",".join(map(str, row)))


if __name__ == "__main__":
    main()
