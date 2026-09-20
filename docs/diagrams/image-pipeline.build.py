#!/usr/bin/env python3
"""Editable source for docs/diagrams/image-pipeline.svg.

Assembles a self-contained SVG that embeds official AWS Architecture Icons
(from jajera/aws-icons) as base64, so the export renders on GitHub Pages with no
external fetches. This is the diagram's editable source — edit here, regenerate,
then copy the SVG into src/assets/diagrams/ for the site to import.

Regenerate (run from the repo root):

    base=https://raw.githubusercontent.com/jajera/aws-icons/main
    mkdir -p /tmp/icons
    curl -s $base/icons/service/developer/Arch_AWS-CodeBuild_64.svg                         -o /tmp/icons/codebuild.svg
    curl -s $base/icons/service/containers/Arch_Amazon-Elastic-Container-Registry_64.svg    -o /tmp/icons/ecr.svg
    curl -s $base/icons/resource/compute/Res_Amazon-EC2_Instance_48.svg                     -o /tmp/icons/ec2.svg
    curl -s $base/icons/resource/storage/Res_Amazon-Simple-Storage-Service_Bucket_48.svg    -o /tmp/icons/s3src.svg
    ICON_DIR=/tmp/icons python3 docs/diagrams/image-pipeline.build.py
    cp docs/diagrams/image-pipeline.svg src/assets/diagrams/image-pipeline.svg
"""
import base64
import os
import pathlib

ICON_DIR = pathlib.Path(os.environ.get("ICON_DIR", ".lab/icons"))
OUT = pathlib.Path("docs/diagrams/image-pipeline.svg")


def data_uri(name: str) -> str:
    raw = (ICON_DIR / f"{name}.svg").read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


ICONS = {k: data_uri(k) for k in ("codebuild", "ecr", "ec2", "s3src")}

# Layout constants
W, H = 940, 380
NODE = 64

def node(x, y, icon, label, sub=""):
    ix = x - NODE / 2
    sub_line = (
        f'<text x="{x}" y="{y + 94}" class="sub">{sub}</text>' if sub else ""
    )
    return f"""
  <g>
    <image x="{ix}" y="{y}" width="{NODE}" height="{NODE}" href="{ICONS[icon]}"/>
    <text x="{x}" y="{y + 80}" class="lbl">{label}</text>
    {sub_line}
  </g>"""


def arrow(x1, y1, x2, y2, label, dashed=False, mid_dy=-8):
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2 + mid_dy
    return f"""
  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="edge"{dash} marker-end="url(#arrow)"/>
  <text x="{mx}" y="{my}" class="edgelbl">{label}</text>"""


# Node coordinates (icon top-left anchor y; label sits below)
Y = 80
OP_X, CB_X, ECR_X, EC2_X = 90, 340, 590, 840
SRC_X, SRC_Y = 200, 250

svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica, Arial, sans-serif">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#5a6b7b"/>
    </marker>
    <style>
      .lbl {{ font-size: 13px; font-weight: 600; fill: #232f3e; text-anchor: middle; }}
      .sub {{ font-size: 11px; fill: #5a6b7b; text-anchor: middle; }}
      .edge {{ stroke: #5a6b7b; stroke-width: 2; fill: none; }}
      .edgelbl {{ font-size: 11px; fill: #5a6b7b; text-anchor: middle; }}
      .title {{ font-size: 14px; font-weight: 700; fill: #232f3e; }}
      .legend {{ font-size: 11px; fill: #5a6b7b; }}
    </style>
  </defs>

  <text x="24" y="34" class="title">Harness image pipeline (durable) &#183; ap-southeast-2</text>

  <!-- operator: simple laptop glyph, no AWS icon needed -->
  <g>
    <rect x="{OP_X - 32}" y="{Y}" width="64" height="40" rx="4" fill="#ffffff" stroke="#879596" stroke-width="2"/>
    <rect x="{OP_X - 42}" y="{Y + 42}" width="84" height="7" rx="2" fill="#879596"/>
    <text x="{OP_X}" y="{Y + 80}" class="lbl">Operator</text>
    <text x="{OP_X}" y="{Y + 94}" class="sub">image.sh</text>
  </g>
{node(CB_X, Y, "codebuild", "CodeBuild", "arm64 build")}
{node(ECR_X, Y, "ecr", "ECR", "s3x-hotlookup-harness")}
{node(EC2_X, Y, "ec2", "EC2 m7g.large", "later, in lab run")}
{node(SRC_X, SRC_Y, "s3src", "Source bucket", "harness/ zip")}

{arrow(OP_X + 40, Y + 32, CB_X - 40, Y + 32, "start build")}
{arrow(OP_X + 8, Y + 50, SRC_X - 36, SRC_Y + 14, "upload zip", mid_dy=30)}
{arrow(SRC_X + 40, SRC_Y + 6, CB_X - 30, Y + NODE - 4, "source", mid_dy=6)}
{arrow(CB_X + 40, Y + 32, ECR_X - 40, Y + 32, "push image")}
{arrow(ECR_X + 40, Y + 32, EC2_X - 40, Y + 32, "docker pull", dashed=True)}

  <!-- legend -->
  <line x1="470" y1="330" x2="500" y2="330" class="edge"/>
  <text x="506" y="334" class="legend">build/push (this page)</text>
  <line x1="670" y1="330" x2="700" y2="330" class="edge" stroke-dasharray="6 5"/>
  <text x="706" y="334" class="legend">pull during lab run (later)</text>
</svg>
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(svg, encoding="utf-8")
print(f"wrote {OUT} ({len(svg)} bytes)")
