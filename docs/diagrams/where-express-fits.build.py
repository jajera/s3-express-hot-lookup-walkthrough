#!/usr/bin/env python3
"""Editable source for docs/diagrams/where-express-fits.svg.

Assembles a self-contained SVG that embeds official AWS Architecture Icons
(from jajera/aws-icons) as base64, so the export renders on GitHub Pages with no
external fetches. This is the diagram's editable source — edit here, regenerate,
then copy the SVG into src/assets/diagrams/ for the site to import.

Guidance view of the failure domain: the Express directory bucket lives in ONE
AZ (its blast radius), while a multi-AZ Standard copy (or regenerable source) is
the authoritative store. The application reads hot GETs from Express but rebuilds
or falls back to the durable copy; an AZ-wide event can lose Express objects.

Regenerate (run from the repo root):

    base=https://raw.githubusercontent.com/jajera/aws-icons/main
    mkdir -p /tmp/icons
    curl -s $base/icons/resource/storage/Res_Amazon-Simple-Storage-Service_Directory-bucket_48.svg   -o /tmp/icons/s3dir.svg
    curl -s $base/icons/resource/storage/Res_Amazon-Simple-Storage-Service_S3-Standard_48.svg         -o /tmp/icons/s3std.svg
    curl -s $base/icons/resource/general/Res_Generic-Application_48_Light.svg                         -o /tmp/icons/app.svg
    curl -s $base/icons/group/general/Region_32.svg                                                   -o /tmp/icons/gRegion.svg
    ICON_DIR=/tmp/icons python3 docs/diagrams/where-express-fits.build.py
    cp docs/diagrams/where-express-fits.svg src/assets/diagrams/where-express-fits.svg
"""
import base64
import os
import pathlib

ICON_DIR = pathlib.Path(os.environ.get("ICON_DIR", ".lab/icons"))
OUT = pathlib.Path("docs/diagrams/where-express-fits.svg")


def data_uri(name: str) -> str:
    raw = (ICON_DIR / f"{name}.svg").read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


ICONS = {k: data_uri(k) for k in ("s3dir", "s3std", "app", "gRegion")}

W, H = 780, 410
NODE = 52


def node(x, y, icon, label, sub="", size=NODE):
    ix = x - size / 2
    sub_line = (
        f'<text x="{x}" y="{y + size + 30}" class="sub">{sub}</text>' if sub else ""
    )
    return f"""
  <g>
    <image x="{ix}" y="{y}" width="{size}" height="{size}" href="{ICONS[icon]}"/>
    <text x="{x}" y="{y + size + 16}" class="lbl">{label}</text>
    {sub_line}
  </g>"""


def plate(lx, ly, w, txt, cls="edgelbl", fill="#ffffff"):
    return (
        f'<rect x="{lx - w/2}" y="{ly - 11}" width="{w}" height="16" rx="3" '
        f'fill="{fill}" opacity="0.92"/>'
        f'<text x="{lx}" y="{ly}" class="{cls}">{txt}</text>'
    )


# --- coordinates ---------------------------------------------------------
# Left-to-right, no crossing lines. Region hugs its content (no dead space):
#   Application (left)  ->  Region { Standard (top) ; AZ box + Express (bottom) }
APP_X, APP_Y = 90, 180

REG_X, REG_Y, REG_W, REG_H = 300, 56, 440, 320  # bottom = 376

# Standard copy in the Region (top row): icon 96-148, label 164, sub 178
STD_X, STD_Y = 430, 96
# AZ failure-domain box: 196 -> 352 (bottom), 24px padding to Region bottom (376)
AZ_X, AZ_Y, AZ_W, AZ_H = 330, 196, 380, 156
# directory bucket inside AZ: header baseline 216, icon starts 228 (clear of header)
DIR_X, DIR_Y = 430, 228
# re-seed runs down the right side, clear of both sub-labels
RESEED_X = 620

svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica, Arial, sans-serif">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#5a6b7b"/>
    </marker>
    <style>
      .lbl {{ font-size: 12px; font-weight: 600; fill: #232f3e; text-anchor: middle; }}
      .sub {{ font-size: 10.5px; fill: #5a6b7b; text-anchor: middle; }}
      .edge {{ stroke: #5a6b7b; stroke-width: 2; fill: none; }}
      .edgelbl {{ font-size: 10.5px; fill: #5a6b7b; text-anchor: middle; }}
      .title {{ font-size: 14px; font-weight: 700; fill: #232f3e; }}
      .grp {{ font-size: 12px; font-weight: 700; }}
      .grpsub {{ font-size: 10.5px; fill: #5a6b7b; }}
      .legend {{ font-size: 10.5px; fill: #5a6b7b; }}
    </style>
  </defs>

  <!-- self-contained light surface so the diagram reads on any page theme -->
  <rect id="s3x-surface" x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="#ffffff" stroke="#d6dde5" stroke-width="1"/>

  <text x="24" y="32" class="title">Express is single-AZ</text>
  <text x="24" y="50" class="grpsub" fill="#c0392b">Never leave the only copy of important data in Express.</text>

  <!-- Application (left) -->
{node(APP_X, APP_Y, "app", "Application", "reads + rebuilds")}

  <!-- Region container (right) -->
  <rect x="{REG_X}" y="{REG_Y}" width="{REG_W}" height="{REG_H}" rx="8" fill="none" stroke="#00A4A6" stroke-width="2"/>
  <image x="{REG_X + 8}" y="{REG_Y + 8}" width="24" height="24" href="{ICONS['gRegion']}"/>
  <text x="{REG_X + 40}" y="{REG_Y + 26}" class="grp" fill="#007f80">Region ap-southeast-2</text>

  <!-- Multi-AZ Standard copy (top row) -->
{node(STD_X, STD_Y, "s3std", "Standard / source", "multi-AZ, authoritative")}

  <!-- AZ failure-domain box (bottom) with the directory bucket -->
  <rect x="{AZ_X}" y="{AZ_Y}" width="{AZ_W}" height="{AZ_H}" rx="6" fill="#fbecea" stroke="#c0392b" stroke-width="2" stroke-dasharray="2 3"/>
  <text x="{AZ_X + 14}" y="{AZ_Y + 20}" class="grp" fill="#c0392b">AZ apse2-az1 &#183; failure domain</text>
{node(DIR_X, DIR_Y, "s3dir", "Directory bucket", "Express One Zone")}
  <text x="{AZ_X + AZ_W/2}" y="{AZ_Y + AZ_H - 10}" class="edgelbl" fill="#c0392b">&#9888; AZ-wide event can lose these objects</text>

  <!-- edges (all short, non-crossing) -->
  <!-- app -> Standard (authoritative / rebuild), upper -->
{f'<line x1="{APP_X + 28}" y1="{APP_Y + 8}" x2="{STD_X - 30}" y2="{STD_Y + 34}" class="edge" marker-end="url(#arrow)"/>'}
  {plate(245, 128, 148, "authoritative / rebuild")}

  <!-- app -> Express (hot GETs), lower -->
{f'<line x1="{APP_X + 28}" y1="{APP_Y + 30}" x2="{AZ_X - 6}" y2="{DIR_Y + 26}" class="edge" marker-end="url(#arrow)"/>'}
  {plate(240, 232, 78, "hot GETs")}

  <!-- Standard -> Express re-seed: dashed elbow that leaves the Standard icon's
       right edge, drops down the RESEED_X gutter, and enters the directory
       bucket's right edge. RESEED_X sits right of both sub-labels. -->
{f'''<path d="M {STD_X + 24} {STD_Y + NODE/2} H {RESEED_X} V {DIR_Y + NODE/2} H {DIR_X + 28}"
        class="edge" stroke-dasharray="6 5" fill="none" marker-end="url(#arrow)"/>'''}
  {plate(RESEED_X, STD_Y + NODE + 26, 96, "copy / re-seed", fill="#ffffff")}

  <!-- legend -->
  <line x1="24" y1="{H - 12}" x2="54" y2="{H - 12}" class="edge"/>
  <text x="60" y="{H - 8}" class="legend">runtime read</text>
  <line x1="188" y1="{H - 12}" x2="218" y2="{H - 12}" class="edge" stroke-dasharray="6 5"/>
  <text x="224" y="{H - 8}" class="legend">re-seed from the durable copy</text>
</svg>
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(svg, encoding="utf-8")
print(f"wrote {OUT} ({len(svg)} bytes)")
