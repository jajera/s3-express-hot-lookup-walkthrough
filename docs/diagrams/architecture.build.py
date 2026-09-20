#!/usr/bin/env python3
"""Editable source for docs/diagrams/architecture.svg.

Assembles a self-contained SVG that embeds official AWS Architecture Icons
(from jajera/aws-icons) as base64, so the export renders on GitHub Pages with no
external fetches. This is the diagram's editable source — edit here, regenerate,
then copy the SVG into src/assets/diagrams/ for the site to import.

Top-level lab view: durable image pipeline (CodeBuild → ECR) feeds the same-AZ
bakeoff — EC2 harness in a dedicated VPC GETs identical keys from Standard and
the Express directory bucket via dual gateway endpoints; dashboard on :8080.

Regenerate (run from the repo root):

    base=https://raw.githubusercontent.com/jajera/aws-icons/main
    mkdir -p .lab/icons
    curl -s $base/icons/service/developer/Arch_AWS-CodeBuild_64.svg                         -o .lab/icons/codebuild.svg
    curl -s $base/icons/service/containers/Arch_Amazon-Elastic-Container-Registry_64.svg    -o .lab/icons/ecr.svg
    curl -s $base/icons/resource/compute/Res_Amazon-EC2_Instance_48.svg                     -o .lab/icons/ec2.svg
    curl -s $base/icons/resource/containers/Res_Amazon-Elastic-Container-Service_Container-1_48.svg -o .lab/icons/container.svg
    curl -s $base/icons/resource/storage/Res_Amazon-Simple-Storage-Service_S3-Standard_48.svg        -o .lab/icons/s3std.svg
    curl -s $base/icons/resource/storage/Res_Amazon-Simple-Storage-Service_Directory-bucket_48.svg   -o .lab/icons/s3dir.svg
    curl -s $base/icons/resource/networking/Res_Amazon-VPC_Endpoints_48.svg                 -o .lab/icons/vpce.svg
    curl -s $base/icons/group/networking/Virtual-private-cloud-VPC_32.svg                   -o .lab/icons/gVpc.svg
    curl -s $base/icons/group/networking/Public-subnet_32.svg                               -o .lab/icons/gSubnet.svg
    ICON_DIR=.lab/icons python3 docs/diagrams/architecture.build.py
    cp docs/diagrams/architecture.svg src/assets/diagrams/architecture.svg
"""
import base64
import os
import pathlib

ICON_DIR = pathlib.Path(os.environ.get("ICON_DIR", ".lab/icons"))
OUT = pathlib.Path("docs/diagrams/architecture.svg")


def data_uri(name: str) -> str:
    raw = (ICON_DIR / f"{name}.svg").read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


ICONS = {
    k: data_uri(k)
    for k in (
        "codebuild",
        "ecr",
        "ec2",
        "container",
        "s3std",
        "s3dir",
        "vpce",
        "gVpc",
        "gSubnet",
    )
}

W, H = 980, 580
SZ = 48  # icon size for service/resource nodes


def node(cx, top, icon, label, sub="", size=SZ):
    """cx = horizontal centre; top = icon top edge."""
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


def hline(x1, x2, y, label="", dashed=False, label_dy=-8):
    """Strictly horizontal edge; arrow at x2."""
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    lbl = ""
    if label:
        mx = (x1 + x2) / 2
        lbl = f'<text x="{mx}" y="{y + label_dy}" class="edgelbl">{label}</text>'
    return f"""
  <line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" class="edge"{dash} marker-end="url(#arrow)"/>
  {lbl}"""


def vline(x, y1, y2, label="", dashed=False, label_dx=10):
    """Strictly vertical edge; arrow at y2."""
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    lbl = ""
    if label:
        my = (y1 + y2) / 2
        lbl = f'<text x="{x + label_dx}" y="{my}" class="edgelbl">{label}</text>'
    return f"""
  <line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" class="edge"{dash} marker-end="url(#arrow)"/>
  {lbl}"""


def elbow_down_left(x_top, y_top, x_left, y_left, label="", dashed=False):
    """Vertical down from (x_top,y_top) to (x_top,y_left), then left to (x_left,y_left)."""
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    lbl = ""
    if label:
        lbl = f'<text x="{x_top + 10}" y="{(y_top + y_left) / 2}" class="edgelbl">{label}</text>'
    return f"""
  <line x1="{x_top}" y1="{y_top}" x2="{x_top}" y2="{y_left}" class="edge"{dash}/>
  <line x1="{x_top}" y1="{y_left}" x2="{x_left}" y2="{y_left}" class="edge"{dash} marker-end="url(#arrow)"/>
  {lbl}"""


def elbow_down_left_down(x1, y1, y_mid, x2, y2, label="", dashed=False):
    """Down to y_mid, left to x2, down to y2 — keeps the pull path clear of mid-row icons."""
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    lbl = ""
    if label:
        lbl = f'<text x="{(x1 + x2) / 2}" y="{y_mid - 8}" class="edgelbl">{label}</text>'
    return f"""
  <line x1="{x1}" y1="{y1}" x2="{x1}" y2="{y_mid}" class="edge"{dash}/>
  <line x1="{x1}" y1="{y_mid}" x2="{x2}" y2="{y_mid}" class="edge"{dash}/>
  <line x1="{x2}" y1="{y_mid}" x2="{x2}" y2="{y2}" class="edge"{dash} marker-end="url(#arrow)"/>
  {lbl}"""


def elbow_right_vert_right(x1, y1, x_mid, y2, x2, dashed=False):
    """Right to x_mid, vertical to y2, right to x2 (arrow). All axis-aligned."""
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    return f"""
  <line x1="{x1}" y1="{y1}" x2="{x_mid}" y2="{y1}" class="edge"{dash}/>
  <line x1="{x_mid}" y1="{y1}" x2="{x_mid}" y2="{y2}" class="edge"{dash}/>
  <line x1="{x_mid}" y1="{y2}" x2="{x2}" y2="{y2}" class="edge"{dash} marker-end="url(#arrow)"/>"""


def label_plate(lx, ly, w, txt):
    return (
        f'<rect x="{lx - w / 2}" y="{ly - 11}" width="{w}" height="16" rx="3" '
        f'fill="#ffffff" opacity="0.92"/>'
        f'<text x="{lx}" y="{ly}" class="edgelbl">{txt}</text>'
    )


# --- grid ---------------------------------------------------------------
# Pipeline row (icon tops aligned)
PIPE_TOP = 64
OP_CX, CB_CX, ECR_CX = 80, 250, 420
PIPE_MID = PIPE_TOP + 24  # horizontal arrow through icon centres

# VPC / subnet
VPC_X, VPC_Y, VPC_W, VPC_H = 40, 188, 560, 300
SUB_X, SUB_Y, SUB_W, SUB_H = 60, 248, 320, 200

# Runtime row inside subnet (EC2 + harness aligned)
RUN_TOP = 300
EC2_CX, HARNESS_CX = 130, 260
RUN_MID = RUN_TOP + SZ / 2  # 324

# Gateway endpoints sit below the GET lane so horizontals stay clear
VPCE_CX, VPCE_TOP = 470, 390
VPCE_MID = VPCE_TOP + SZ / 2  # 414

# Buckets — stacked right; GETs elbow from harness mid
BUCKET_CX = 800
STD_TOP = 230
DIR_TOP = 390  # mid aligns with VPCE_MID for a straight dashed hop
STD_MID = STD_TOP + SZ / 2  # 254
DIR_MID = DIR_TOP + SZ / 2  # 414
# Branch columns (orthogonal turns)
GET_BRANCH_X = 600
VPCE_BRANCH_X = 640

# Dashboard centred under harness
DASH_CX, DASH_TOP, DASH_W, DASH_H = 260, 520, 260, 40

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
      .strip {{ font-size: 11px; font-weight: 700; fill: #5a6b7b; }}
    </style>
  </defs>

  <text x="24" y="28" class="title">S3 Express hot lookup lab &#183; ap-southeast-2 &#183; apse2-az1</text>
  <text x="24" y="50" class="strip">Durable image pipeline (image.sh)</text>

  <!-- operator laptop -->
  <g>
    <rect x="{OP_CX - 28}" y="{PIPE_TOP + 4}" width="56" height="36" rx="4" fill="#ffffff" stroke="#879596" stroke-width="2"/>
    <rect x="{OP_CX - 36}" y="{PIPE_TOP + 42}" width="72" height="6" rx="2" fill="#879596"/>
    <text x="{OP_CX}" y="{PIPE_TOP + 70}" class="lbl">Operator</text>
    <text x="{OP_CX}" y="{PIPE_TOP + 84}" class="sub">image.sh · demo.sh</text>
  </g>
{node(CB_CX, PIPE_TOP, "codebuild", "CodeBuild", "arm64 build")}
{node(ECR_CX, PIPE_TOP, "ecr", "ECR", "s3x-hotlookup-harness")}

{hline(OP_CX + 30, CB_CX - SZ / 2 - 2, PIPE_MID, "build")}
{hline(CB_CX + SZ / 2 + 2, ECR_CX - SZ / 2 - 2, PIPE_MID, "push")}

  <!-- VPC -->
  <rect x="{VPC_X}" y="{VPC_Y}" width="{VPC_W}" height="{VPC_H}" rx="8" fill="none" stroke="#8C4FFF" stroke-width="2"/>
  <image x="{VPC_X + 8}" y="{VPC_Y + 8}" width="22" height="22" href="{ICONS['gVpc']}"/>
  <text x="{VPC_X + 38}" y="{VPC_Y + 18}" class="grp" fill="#8C4FFF">VPC</text>
  <text x="{VPC_X + 38}" y="{VPC_Y + 32}" class="grpsub">10.87.0.0/16 &#183; demo.sh up</text>

  <!-- Public subnet -->
  <rect x="{SUB_X}" y="{SUB_Y}" width="{SUB_W}" height="{SUB_H}" rx="6" fill="#f2f8ea" stroke="#7AA116" stroke-width="2"/>
  <image x="{SUB_X + 8}" y="{SUB_Y + 8}" width="20" height="20" href="{ICONS['gSubnet']}"/>
  <text x="{SUB_X + 34}" y="{SUB_Y + 22}" class="grp" fill="#5c7a10">Public subnet &#183; apse2-az1</text>

{node(EC2_CX, RUN_TOP, "ec2", "EC2", "m7g.large")}
{node(HARNESS_CX, RUN_TOP, "container", "Harness", ":8080")}
{node(VPCE_CX, VPCE_TOP, "vpce", "Gateway EPs", "s3 + s3express")}

  <!-- ECR → EC2: down, left above the runtime row, then down into EC2 -->
{elbow_down_left_down(ECR_CX, PIPE_TOP + SZ + 30, SUB_Y + 28, EC2_CX, RUN_TOP, "docker pull", dashed=True)}

  <!-- EC2 → harness (horizontal) -->
{hline(EC2_CX + SZ / 2 + 2, HARNESS_CX - SZ / 2 - 2, RUN_MID)}

  <!-- buckets -->
{node(BUCKET_CX, STD_TOP, "s3std", "Standard bucket", "bakeoff baseline")}
{node(BUCKET_CX, DIR_TOP, "s3dir", "Directory bucket", "Express One Zone")}

  <!-- harness GETs: right → branch → up/down → buckets (clear of VPCE) -->
{elbow_right_vert_right(HARNESS_CX + SZ / 2 + 2, RUN_MID, GET_BRANCH_X, STD_MID, BUCKET_CX - SZ / 2 - 2)}
{elbow_right_vert_right(HARNESS_CX + SZ / 2 + 2, RUN_MID, GET_BRANCH_X, DIR_MID, BUCKET_CX - SZ / 2 - 2)}
  {label_plate(700, STD_MID - 10, 46, "GET")}
  {label_plate(700, DIR_MID - 10, 156, "GET + CreateSession")}

  <!-- gateway endpoint paths (dashed from VPCE row) -->
{elbow_right_vert_right(VPCE_CX + SZ / 2 + 2, VPCE_MID, VPCE_BRANCH_X, STD_MID, BUCKET_CX - SZ / 2 - 2, dashed=True)}
{hline(VPCE_CX + SZ / 2 + 2, BUCKET_CX - SZ / 2 - 2, DIR_MID, dashed=True)}

  <!-- dashboard (vertical from harness) -->
  <rect x="{DASH_CX - DASH_W / 2}" y="{DASH_TOP}" width="{DASH_W}" height="{DASH_H}" rx="6" fill="#ffffff" stroke="#232f3e" stroke-width="1.5"/>
  <text x="{DASH_CX}" y="{DASH_TOP + 16}" class="kv">Dashboard &#183; /api/stats</text>
  <text x="{DASH_CX}" y="{DASH_TOP + 32}" class="sub">p50 / p90 &#183; Standard &#247; Express</text>
{vline(HARNESS_CX, RUN_TOP + SZ + 30, DASH_TOP)}

  <!-- legend -->
  <line x1="560" y1="{H - 16}" x2="590" y2="{H - 16}" class="edge"/>
  <text x="596" y="{H - 12}" class="legend">lab runtime (demo.sh)</text>
  <line x1="760" y1="{H - 16}" x2="790" y2="{H - 16}" class="edge" stroke-dasharray="6 5"/>
  <text x="796" y="{H - 12}" class="legend">image pull / gateway path</text>
</svg>
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(svg, encoding="utf-8")
print(f"wrote {OUT} ({len(svg)} bytes)")
