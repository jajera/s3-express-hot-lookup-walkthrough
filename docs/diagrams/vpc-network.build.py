#!/usr/bin/env python3
"""Editable source for docs/diagrams/vpc-network.svg.

Assembles a self-contained SVG that embeds official AWS Architecture Icons
(from jajera/aws-icons) as base64, so the export renders on GitHub Pages with no
external fetches. This is the diagram's editable source — edit here, regenerate,
then copy the SVG into src/assets/diagrams/ for the site to import.

Shows the dedicated lab VPC: public subnet in apse2-az1, internet gateway with a
default route, and the two S3 gateway endpoints (s3 + s3express) that the route
table points at the Standard and directory buckets.

Regenerate (run from the repo root):

    base=https://raw.githubusercontent.com/jajera/aws-icons/main
    mkdir -p /tmp/icons
    curl -s $base/icons/resource/networking/Res_Amazon-VPC_Internet-Gateway_48.svg          -o /tmp/icons/igw.svg
    curl -s $base/icons/resource/networking/Res_Amazon-VPC_Endpoints_48.svg                 -o /tmp/icons/vpce.svg
    curl -s $base/icons/resource/networking/Res_Amazon-VPC_Router_48.svg                    -o /tmp/icons/router.svg
    curl -s $base/icons/resource/storage/Res_Amazon-Simple-Storage-Service_S3-Standard_48.svg        -o /tmp/icons/s3std.svg
    curl -s $base/icons/resource/storage/Res_Amazon-Simple-Storage-Service_Directory-bucket_48.svg   -o /tmp/icons/s3dir.svg
    curl -s $base/icons/group/networking/Virtual-private-cloud-VPC_32.svg                   -o /tmp/icons/gVpc.svg
    curl -s $base/icons/group/networking/Public-subnet_32.svg                               -o /tmp/icons/gSubnet.svg
    ICON_DIR=/tmp/icons python3 docs/diagrams/vpc-network.build.py
    cp docs/diagrams/vpc-network.svg src/assets/diagrams/vpc-network.svg
"""
import base64
import os
import pathlib

ICON_DIR = pathlib.Path(os.environ.get("ICON_DIR", ".lab/icons"))
OUT = pathlib.Path("docs/diagrams/vpc-network.svg")


def data_uri(name: str) -> str:
    raw = (ICON_DIR / f"{name}.svg").read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


ICONS = {
    k: data_uri(k)
    for k in ("igw", "vpce", "router", "s3std", "s3dir", "gVpc", "gSubnet")
}

W, H = 940, 500
NODE = 56


def node(x, y, icon, label, sub=""):
    ix = x - NODE / 2
    sub_line = (
        f'<text x="{x}" y="{y + 88}" class="sub">{sub}</text>' if sub else ""
    )
    return f"""
  <g>
    <image x="{ix}" y="{y}" width="{NODE}" height="{NODE}" href="{ICONS[icon]}"/>
    <text x="{x}" y="{y + 74}" class="lbl">{label}</text>
    {sub_line}
  </g>"""


def arrow(x1, y1, x2, y2, label="", dashed=False, mid_dx=0, mid_dy=-8):
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    lbl = ""
    if label:
        mx = (x1 + x2) / 2 + mid_dx
        my = (y1 + y2) / 2 + mid_dy
        lbl = f'<text x="{mx}" y="{my}" class="edgelbl">{label}</text>'
    return f"""
  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="edge"{dash} marker-end="url(#arrow)"/>
  {lbl}"""


# --- coordinates ---------------------------------------------------------
# VPC container
VPC_X, VPC_Y, VPC_W, VPC_H = 30, 60, 560, 400
# Public subnet container (inside VPC)
SUB_X, SUB_Y, SUB_W, SUB_H = 60, 220, 320, 210

# nodes inside subnet
IGW_X, IGW_Y = 400, 96       # internet gateway near VPC top (out of subnet header)
RTB_X, RTB_Y = 135, 285      # route table / router
VPCE_X, VPCE_Y = 305, 285    # both gateway endpoints (one glyph, two labels)

# S3 targets (outside the VPC — the AWS service side)
STD_X, STD_Y = 750, 210
DIR_X, DIR_Y = 750, 350

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

  <text x="24" y="34" class="title">Dedicated lab VPC &#183; ap-southeast-2 &#183; apse2-az1</text>

  <!-- VPC container -->
  <rect x="{VPC_X}" y="{VPC_Y}" width="{VPC_W}" height="{VPC_H}" rx="8" fill="none" stroke="#8C4FFF" stroke-width="2"/>
  <image x="{VPC_X + 8}" y="{VPC_Y + 8}" width="26" height="26" href="{ICONS['gVpc']}"/>
  <text x="{VPC_X + 42}" y="{VPC_Y + 20}" class="grp" fill="#8C4FFF">VPC</text>
  <text x="{VPC_X + 42}" y="{VPC_Y + 34}" class="grpsub">10.87.0.0/16</text>

  <!-- Public subnet container -->
  <rect x="{SUB_X}" y="{SUB_Y}" width="{SUB_W}" height="{SUB_H}" rx="6" fill="#f2f8ea" stroke="#7AA116" stroke-width="2"/>
  <image x="{SUB_X + 8}" y="{SUB_Y + 8}" width="24" height="24" href="{ICONS['gSubnet']}"/>
  <text x="{SUB_X + 38}" y="{SUB_Y + 19}" class="grp" fill="#5c7a10">Public subnet</text>
  <text x="{SUB_X + 38}" y="{SUB_Y + 33}" class="grpsub">10.87.1.0/24 &#183; apse2-az1</text>

  <!-- Internet gateway on the VPC boundary -->
{node(IGW_X, IGW_Y, "igw", "Internet gateway", "default route 0.0.0.0/0")}

  <!-- route table / router inside subnet -->
{node(RTB_X, RTB_Y, "router", "Route table", "public-rt")}

  <!-- gateway endpoints (single glyph, two services) -->
{node(VPCE_X, VPCE_Y, "vpce", "Gateway endpoints", "s3 + s3express")}

  <!-- S3 service targets outside the VPC -->
{node(STD_X, STD_Y, "s3std", "Standard bucket", "general purpose")}
{node(DIR_X, DIR_Y, "s3dir", "Directory bucket", "Express One Zone")}

  <!-- edges -->
{arrow(IGW_X - 20, IGW_Y + NODE - 6, RTB_X + 20, RTB_Y, "default route", mid_dx=40, mid_dy=-4)}
{arrow(RTB_X + 34, RTB_Y + 28, VPCE_X - 34, VPCE_Y + 28, "route", mid_dy=-6)}
{arrow(VPCE_X + 30, VPCE_Y + 10, STD_X - 34, STD_Y + 34, "s3", dashed=True, mid_dy=-6)}
{arrow(VPCE_X + 30, VPCE_Y + 40, DIR_X - 34, DIR_Y + 20, "s3express", dashed=True, mid_dy=18)}

  <!-- legend -->
  <line x1="{VPC_X}" y1="{H - 14}" x2="{VPC_X + 30}" y2="{H - 14}" class="edge"/>
  <text x="{VPC_X + 36}" y="{H - 10}" class="legend">inside the VPC</text>
  <line x1="{VPC_X + 170}" y1="{H - 14}" x2="{VPC_X + 200}" y2="{H - 14}" class="edge" stroke-dasharray="6 5"/>
  <text x="{VPC_X + 206}" y="{H - 10}" class="legend">gateway endpoint to the S3 service</text>
</svg>
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(svg, encoding="utf-8")
print(f"wrote {OUT} ({len(svg)} bytes)")
