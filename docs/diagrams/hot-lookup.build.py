#!/usr/bin/env python3
"""Editable source for docs/diagrams/hot-lookup.svg.

Landing-page story: co-located compute GETs the same hot keys from an Express
directory bucket and a Standard general-purpose bucket — the shared hot lookup
bakeoff this lab proves.

Regenerate (run from the repo root):

    base=https://raw.githubusercontent.com/jajera/aws-icons/main
    mkdir -p .lab/icons
    curl -s $base/icons/resource/compute/Res_Amazon-EC2_Instance_48.svg                     -o .lab/icons/ec2.svg
    curl -s $base/icons/resource/containers/Res_Amazon-Elastic-Container-Service_Container-1_48.svg -o .lab/icons/container.svg
    curl -s $base/icons/resource/storage/Res_Amazon-Simple-Storage-Service_S3-Standard_48.svg        -o .lab/icons/s3std.svg
    curl -s $base/icons/resource/storage/Res_Amazon-Simple-Storage-Service_Directory-bucket_48.svg   -o .lab/icons/s3dir.svg
    curl -s $base/icons/group/networking/Virtual-private-cloud-VPC_32.svg                   -o .lab/icons/gVpc.svg
    curl -s $base/icons/group/networking/Public-subnet_32.svg                               -o .lab/icons/gSubnet.svg
    ICON_DIR=.lab/icons python3 docs/diagrams/hot-lookup.build.py
    cp docs/diagrams/hot-lookup.svg src/assets/diagrams/hot-lookup.svg
"""
import base64
import os
import pathlib

ICON_DIR = pathlib.Path(os.environ.get("ICON_DIR", ".lab/icons"))
OUT = pathlib.Path("docs/diagrams/hot-lookup.svg")


def data_uri(name: str) -> str:
    raw = (ICON_DIR / f"{name}.svg").read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


ICONS = {
    k: data_uri(k)
    for k in ("ec2", "container", "s3std", "s3dir", "gVpc", "gSubnet")
}

W, H = 920, 420
SZ = 52


def node(cx, top, icon, label, sub="", size=SZ):
    ix = cx - size / 2
    sub_line = (
        f'<text x="{cx}" y="{top + size + 28}" class="sub">{sub}</text>' if sub else ""
    )
    return f"""
  <g>
    <image x="{ix}" y="{top}" width="{size}" height="{size}" href="{ICONS[icon]}"/>
    <text x="{cx}" y="{top + size + 14}" class="lbl">{label}</text>
    {sub_line}
  </g>"""


def elbow_right_vert_right(x1, y1, x_mid, y2, x2):
    return f"""
  <line x1="{x1}" y1="{y1}" x2="{x_mid}" y2="{y1}" class="edge"/>
  <line x1="{x_mid}" y1="{y1}" x2="{x_mid}" y2="{y2}" class="edge"/>
  <line x1="{x_mid}" y1="{y2}" x2="{x2}" y2="{y2}" class="edge" marker-end="url(#arrow)"/>"""


def label_plate(lx, ly, w, txt):
    return (
        f'<rect x="{lx - w / 2}" y="{ly - 11}" width="{w}" height="16" rx="3" '
        f'fill="#ffffff" opacity="0.92"/>'
        f'<text x="{lx}" y="{ly}" class="edgelbl">{txt}</text>'
    )


# --- grid ---------------------------------------------------------------
VPC_X, VPC_Y, VPC_W, VPC_H = 40, 56, 380, 300
SUB_X, SUB_Y, SUB_W, SUB_H = 70, 120, 320, 200

EC2_CX, HARNESS_CX = 150, 290
RUN_TOP = 170
RUN_MID = RUN_TOP + SZ / 2

BUCKET_CX = 720
STD_TOP = 100
DIR_TOP = 250
STD_MID = STD_TOP + SZ / 2
DIR_MID = DIR_TOP + SZ / 2
BRANCH_X = 520

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

  <text x="24" y="32" class="title">Shared hot lookup &#183; same-AZ GETs vs Standard</text>

  <rect x="{VPC_X}" y="{VPC_Y}" width="{VPC_W}" height="{VPC_H}" rx="8" fill="none" stroke="#8C4FFF" stroke-width="2"/>
  <image x="{VPC_X + 8}" y="{VPC_Y + 8}" width="22" height="22" href="{ICONS['gVpc']}"/>
  <text x="{VPC_X + 38}" y="{VPC_Y + 18}" class="grp" fill="#8C4FFF">VPC</text>
  <text x="{VPC_X + 38}" y="{VPC_Y + 32}" class="grpsub">ap-southeast-2</text>

  <rect x="{SUB_X}" y="{SUB_Y}" width="{SUB_W}" height="{SUB_H}" rx="6" fill="#f2f8ea" stroke="#7AA116" stroke-width="2"/>
  <image x="{SUB_X + 8}" y="{SUB_Y + 8}" width="20" height="20" href="{ICONS['gSubnet']}"/>
  <text x="{SUB_X + 34}" y="{SUB_Y + 22}" class="grp" fill="#5c7a10">Public subnet &#183; apse2-az1</text>

{node(EC2_CX, RUN_TOP, "ec2", "EC2", "m7g.large")}
{node(HARNESS_CX, RUN_TOP, "container", "Harness", "hot key GETs")}

{node(BUCKET_CX, STD_TOP, "s3std", "Standard bucket", "multi-AZ baseline")}
{node(BUCKET_CX, DIR_TOP, "s3dir", "Directory bucket", "Express One Zone")}

  <!-- EC2 → harness -->
  <line x1="{EC2_CX + SZ / 2 + 2}" y1="{RUN_MID}" x2="{HARNESS_CX - SZ / 2 - 2}" y2="{RUN_MID}" class="edge" marker-end="url(#arrow)"/>

  <!-- harness → buckets (orthogonal) -->
{elbow_right_vert_right(HARNESS_CX + SZ / 2 + 2, RUN_MID, BRANCH_X, STD_MID, BUCKET_CX - SZ / 2 - 2)}
{elbow_right_vert_right(HARNESS_CX + SZ / 2 + 2, RUN_MID, BRANCH_X, DIR_MID, BUCKET_CX - SZ / 2 - 2)}
  {label_plate(600, STD_MID - 10, 100, "GET same keys")}
  {label_plate(600, DIR_MID - 10, 156, "GET + CreateSession")}

  <line x1="24" y1="{H - 16}" x2="54" y2="{H - 16}" class="edge"/>
  <text x="60" y="{H - 12}" class="legend">Co-locate compute with Express for single-digit ms hot lookups</text>
</svg>
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(svg, encoding="utf-8")
print(f"wrote {OUT} ({len(svg)} bytes)")
