#!/usr/bin/env python3
"""Editable source for docs/diagrams/harness.svg.

Assembles a self-contained SVG that embeds official AWS Architecture Icons
(from jajera/aws-icons) as base64, so the export renders on GitHub Pages with no
external fetches. This is the diagram's editable source — edit here, regenerate,
then copy the SVG into src/assets/diagrams/ for the site to import.

Runtime view: identical hot keys are seeded into both buckets, then the harness
container on the lab EC2 (pulled from ECR at boot) issues continuous GETs to
both — CreateSession to the directory bucket, plain GET to Standard — and serves
the dashboard / stats on :8080 with the Standard/Express latency ratio.

Regenerate (run from the repo root):

    base=https://raw.githubusercontent.com/jajera/aws-icons/main
    mkdir -p /tmp/icons
    curl -s $base/icons/resource/compute/Res_Amazon-EC2_Instance_48.svg                                   -o /tmp/icons/ec2.svg
    curl -s $base/icons/resource/containers/Res_Amazon-Elastic-Container-Service_Container-1_48.svg        -o /tmp/icons/container.svg
    curl -s $base/icons/resource/containers/Res_Amazon-Elastic-Container-Registry_Image_48.svg             -o /tmp/icons/ecrimg.svg
    curl -s $base/icons/resource/storage/Res_Amazon-Simple-Storage-Service_S3-Standard_48.svg              -o /tmp/icons/s3std.svg
    curl -s $base/icons/resource/storage/Res_Amazon-Simple-Storage-Service_Directory-bucket_48.svg         -o /tmp/icons/s3dir.svg
    curl -s $base/icons/group/networking/Virtual-private-cloud-VPC_32.svg                                  -o /tmp/icons/gVpc.svg
    curl -s $base/icons/group/networking/Public-subnet_32.svg                                              -o /tmp/icons/gSubnet.svg
    ICON_DIR=/tmp/icons python3 docs/diagrams/harness.build.py
    cp docs/diagrams/harness.svg src/assets/diagrams/harness.svg
"""
import base64
import os
import pathlib

ICON_DIR = pathlib.Path(os.environ.get("ICON_DIR", ".lab/icons"))
OUT = pathlib.Path("docs/diagrams/harness.svg")


def data_uri(name: str) -> str:
    raw = (ICON_DIR / f"{name}.svg").read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


ICONS = {
    k: data_uri(k)
    for k in ("ec2", "container", "ecr", "s3std", "s3dir", "gVpc", "gSubnet")
}

W, H = 960, 480
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


def label_plate(lx, ly, w, txt, cls="edgelbl"):
    return (
        f'<rect x="{lx - w/2}" y="{ly - 11}" width="{w}" height="16" rx="3" '
        f'fill="#ffffff" opacity="0.92"/>'
        f'<text x="{lx}" y="{ly}" class="{cls}">{txt}</text>'
    )


# --- coordinates ---------------------------------------------------------
# Subnet must fit: ECR icon, harness icon, and the harness sub-label
# (drawn at HARNESS_TOP + iconsize + 30). Size the box from those.
VPC_X, VPC_Y, VPC_W, VPC_H = 250, 56, 320, 330
SUB_X, SUB_Y, SUB_W, SUB_H = 275, 132, 270, 232

ECR_X, ECR_Y = 410, 188          # ECR icon (below the subnet header)
HARNESS_CX, HARNESS_TOP = 410, 262   # harness container (48px icon)
# harness sub-label lands at 262 + 48 + 30 = 340; subnet bottom = 132 + 232 = 364 → 24px clear

STD_X, STD_Y = 800, 130          # Standard bucket (right)
DIR_X, DIR_Y = 800, 260          # directory bucket (right)
DASH_X, DASH_Y = 410, 408        # dashboard box, fully below the VPC (VPC bottom = 386)

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
      .kv {{ font-size: 11px; fill: #232f3e; text-anchor: middle; font-weight: 600; }}
    </style>
  </defs>

  <text x="24" y="34" class="title">Bakeoff runtime &#183; harness GETs both buckets on :8080</text>

  <!-- VPC + subnet containers -->
  <rect x="{VPC_X}" y="{VPC_Y}" width="{VPC_W}" height="{VPC_H}" rx="8" fill="none" stroke="#8C4FFF" stroke-width="2"/>
  <image x="{VPC_X + 8}" y="{VPC_Y + 8}" width="22" height="22" href="{ICONS['gVpc']}"/>
  <text x="{VPC_X + 38}" y="{VPC_Y + 24}" class="grp" fill="#8C4FFF">VPC</text>
  <rect x="{SUB_X}" y="{SUB_Y}" width="{SUB_W}" height="{SUB_H}" rx="6" fill="#f2f8ea" stroke="#7AA116" stroke-width="2"/>
  <image x="{SUB_X + 8}" y="{SUB_Y + 8}" width="20" height="20" href="{ICONS['gSubnet']}"/>
  <text x="{SUB_X + 34}" y="{SUB_Y + 22}" class="grp" fill="#5c7a10">EC2 m7g.large &#183; apse2-az1</text>

  <!-- ECR image (pulled at boot) -->
{node(ECR_X, ECR_Y, "ecr", "", size=40)}
  <text x="{ECR_X}" y="{ECR_Y - 8}" class="sub">ECR image</text>

  <!-- harness container -->
{node(HARNESS_CX, HARNESS_TOP, "container", "Harness :8080", "continuous GET loop", size=48)}

  <!-- buckets on the right -->
{node(STD_X, STD_Y, "s3std", "Standard bucket", "baseline")}
{node(DIR_X, DIR_Y, "s3dir", "Directory bucket", "Express One Zone")}

  <!-- dashboard box (bottom) -->
  <rect x="{DASH_X - 150}" y="{DASH_Y}" width="300" height="46" rx="6" fill="#ffffff" stroke="#232f3e" stroke-width="1.5"/>
  <text x="{DASH_X}" y="{DASH_Y + 19}" class="kv">Dashboard &#183; /api/stats</text>
  <text x="{DASH_X}" y="{DASH_Y + 36}" class="sub">p50 / p90 &#183; Standard &#247; Express ratio</text>

  <!-- edges -->
  <!-- ECR image feeds the container (dashed pull at boot) -->
{f'<line x1="{ECR_X}" y1="{ECR_Y + 40}" x2="{HARNESS_CX}" y2="{HARNESS_TOP}" class="edge" stroke-dasharray="6 5" marker-end="url(#arrow)"/>'}

  <!-- harness GETs both buckets (both exit the container's right edge) -->
{f'<line x1="{HARNESS_CX + 25}" y1="{HARNESS_TOP + 14}" x2="{STD_X - 30}" y2="{STD_Y + 32}" class="edge" marker-end="url(#arrow)"/>'}
{f'<line x1="{HARNESS_CX + 25}" y1="{HARNESS_TOP + 30}" x2="{DIR_X - 30}" y2="{DIR_Y + 22}" class="edge" marker-end="url(#arrow)"/>'}

  <!-- harness -> dashboard -->
{f'<line x1="{HARNESS_CX}" y1="{HARNESS_TOP + 48}" x2="{DASH_X}" y2="{DASH_Y}" class="edge" marker-end="url(#arrow)"/>'}

  <!-- edge labels with plates, placed on the clear part of each GET line near the buckets -->
  {label_plate(690, 168, 46, "GET")}
  {label_plate(660, 268, 156, "GET + CreateSession")}

  <!-- legend -->
  <line x1="24" y1="{H - 12}" x2="54" y2="{H - 12}" class="edge"/>
  <text x="60" y="{H - 8}" class="legend">continuous GET (runtime)</text>
  <line x1="230" y1="{H - 12}" x2="260" y2="{H - 12}" class="edge" stroke-dasharray="6 5"/>
  <text x="266" y="{H - 8}" class="legend">image pull at boot</text>
  <text x="460" y="{H - 8}" class="legend">Seed puts identical hot/ keys in both buckets first.</text>
</svg>
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(svg, encoding="utf-8")
print(f"wrote {OUT} ({len(svg)} bytes)")
