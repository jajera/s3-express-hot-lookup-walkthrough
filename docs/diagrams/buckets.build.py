#!/usr/bin/env python3
"""Editable source for docs/diagrams/buckets.svg.

Assembles a self-contained SVG that embeds official AWS Architecture Icons
(from jajera/aws-icons) as base64, so the export renders on GitHub Pages with no
external fetches. This is the diagram's editable source — edit here, regenerate,
then copy the SVG into src/assets/diagrams/ for the site to import.

Side-by-side comparison of the two lab buckets in ap-southeast-2: a Standard
general-purpose bucket (regional, taggable) and an Express directory bucket
(single AZ apse2-az1, name --apse2-az1--x-s3). Both carry the lab Project tag;
directory buckets are tagged via the s3express TagResource path (s3control
tag-resource in the CLI), not the classic s3:PutBucketTagging API.

Regenerate (run from the repo root):

    base=https://raw.githubusercontent.com/jajera/aws-icons/main
    mkdir -p /tmp/icons
    curl -s $base/icons/resource/storage/Res_Amazon-Simple-Storage-Service_S3-Standard_48.svg          -o /tmp/icons/s3std.svg
    curl -s $base/icons/resource/storage/Res_Amazon-Simple-Storage-Service_Directory-bucket_48.svg     -o /tmp/icons/s3dir.svg
    curl -s $base/icons/group/general/Region_32.svg                                                    -o /tmp/icons/gRegion.svg
    ICON_DIR=/tmp/icons python3 docs/diagrams/buckets.build.py
    cp docs/diagrams/buckets.svg src/assets/diagrams/buckets.svg
"""
import base64
import os
import pathlib

ICON_DIR = pathlib.Path(os.environ.get("ICON_DIR", ".lab/icons"))
OUT = pathlib.Path("docs/diagrams/buckets.svg")


def data_uri(name: str) -> str:
    raw = (ICON_DIR / f"{name}.svg").read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


ICONS = {k: data_uri(k) for k in ("s3std", "s3dir", "gRegion")}

W, H = 940, 430
ICN = 52


def card(x, y, w, h, accent, icon, title, sub, rows):
    """A bucket card with an icon, title, and a short property list."""
    lines = ""
    ry = y + 108
    for label, val in rows:
        lines += (
            f'<text x="{x + 20}" y="{ry}" class="rk">{label}</text>'
            f'<text x="{x + w - 20}" y="{ry}" class="rv">{val}</text>'
        )
        ry += 26
    return f"""
  <g>
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#ffffff" stroke="{accent}" stroke-width="2"/>
    <rect x="{x}" y="{y}" width="{w}" height="6" rx="3" fill="{accent}"/>
    <image x="{x + 20}" y="{y + 22}" width="{ICN}" height="{ICN}" href="{ICONS[icon]}"/>
    <text x="{x + 84}" y="{y + 44}" class="ct">{title}</text>
    <text x="{x + 84}" y="{y + 64}" class="cs">{sub}</text>
    <line x1="{x + 20}" y1="{y + 88}" x2="{x + w - 20}" y2="{y + 88}" stroke="#e3e8ee" stroke-width="1"/>
    {lines}
  </g>"""


REG_X, REG_Y, REG_W, REG_H = 30, 60, 880, 300
CARD_W, CARD_H = 380, 240
STD_X, DIR_X = 70, 490
CARD_Y = 96

std = card(
    STD_X, CARD_Y, CARD_W, CARD_H, "#7AA116", "s3std",
    "Standard bucket", "general purpose &#183; bakeoff baseline",
    [
        ("Scope", "Regional (multi-AZ)"),
        ("Name", "s3x-hotlookup-&#8230;"),
        ("Auth", "SigV4 (s3:GetObject)"),
        ("Tagging", "Project tag \u2713"),
    ],
)
dir_ = card(
    DIR_X, CARD_Y, CARD_W, CARD_H, "#8C4FFF", "s3dir",
    "Directory bucket", "S3 Express One Zone",
    [
        ("Scope", "Single AZ \u00b7 apse2-az1"),
        ("Name", "&#8230;--apse2-az1--x-s3"),
        ("Auth", "CreateSession (zonal)"),
        ("Tagging", "Project tag \u2713 (TagResource)"),
    ],
)

svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica, Arial, sans-serif">
  <defs>
    <style>
      .title {{ font-size: 14px; font-weight: 700; fill: #232f3e; }}
      .grp {{ font-size: 12px; font-weight: 700; fill: #007f80; }}
      .ct {{ font-size: 14px; font-weight: 700; fill: #232f3e; }}
      .cs {{ font-size: 11px; fill: #5a6b7b; }}
      .rk {{ font-size: 11.5px; fill: #5a6b7b; text-anchor: start; }}
      .rv {{ font-size: 11.5px; font-weight: 600; fill: #232f3e; text-anchor: end; }}
      .note {{ font-size: 11px; fill: #5a6b7b; text-anchor: middle; }}
    </style>
  </defs>

  <text x="24" y="34" class="title">Two buckets, one bakeoff &#183; ap-southeast-2</text>

  <!-- Region container -->
  <rect x="{REG_X}" y="{REG_Y}" width="{REG_W}" height="{REG_H}" rx="8" fill="none" stroke="#00A4A6" stroke-width="2"/>
  <image x="{REG_X + 8}" y="{REG_Y + 8}" width="26" height="26" href="{ICONS['gRegion']}"/>
  <text x="{REG_X + 42}" y="{REG_Y + 26}" class="grp">Region ap-southeast-2</text>
{std}
{dir_}

  <text x="{W / 2}" y="{REG_Y + REG_H + 34}" class="note">Identical hot keys seeded to both &#183; harness GETs both &#183; dashboard reads the Standard &#247; Express ratio</text>
</svg>
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(svg, encoding="utf-8")
print(f"wrote {OUT} ({len(svg)} bytes)")
