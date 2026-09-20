#!/usr/bin/env python3
"""Editable source for docs/diagrams/iam-and-ec2.svg.

Assembles a self-contained SVG that embeds official AWS Architecture Icons
(from jajera/aws-icons) as base64, so the export renders on GitHub Pages with no
external fetches. This is the diagram's editable source — edit here, regenerate,
then copy the SVG into src/assets/diagrams/ for the site to import.

Shows the m7g.large instance in the public subnet (Express AZ) with its instance
profile granting four scoped permissions: s3express:CreateSession on the
directory bucket, S3 read/write on the Standard bucket, ECR pull for the harness
image, and SSM for Session Manager. User-data pulls from ECR and runs the
harness on :8080.

Regenerate (run from the repo root):

    base=https://raw.githubusercontent.com/jajera/aws-icons/main
    mkdir -p /tmp/icons
    curl -s $base/icons/resource/compute/Res_Amazon-EC2_Instance_48.svg                              -o /tmp/icons/ec2.svg
    curl -s $base/icons/resource/security/Res_AWS-Identity-Access-Management_Role_48.svg              -o /tmp/icons/iamrole.svg
    curl -s $base/icons/resource/management/Res_AWS-Systems-Manager_Session-Manager_48.svg            -o /tmp/icons/ssm.svg
    curl -s $base/icons/service/containers/Arch_Amazon-Elastic-Container-Registry_64.svg              -o /tmp/icons/ecr.svg
    curl -s $base/icons/resource/storage/Res_Amazon-Simple-Storage-Service_S3-Standard_48.svg         -o /tmp/icons/s3std.svg
    curl -s $base/icons/resource/storage/Res_Amazon-Simple-Storage-Service_Directory-bucket_48.svg    -o /tmp/icons/s3dir.svg
    curl -s $base/icons/group/networking/Virtual-private-cloud-VPC_32.svg                             -o /tmp/icons/gVpc.svg
    curl -s $base/icons/group/networking/Public-subnet_32.svg                                         -o /tmp/icons/gSubnet.svg
    ICON_DIR=/tmp/icons python3 docs/diagrams/iam-and-ec2.build.py
    cp docs/diagrams/iam-and-ec2.svg src/assets/diagrams/iam-and-ec2.svg
"""
import base64
import os
import pathlib

ICON_DIR = pathlib.Path(os.environ.get("ICON_DIR", ".lab/icons"))
OUT = pathlib.Path("docs/diagrams/iam-and-ec2.svg")


def data_uri(name: str) -> str:
    raw = (ICON_DIR / f"{name}.svg").read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


ICONS = {
    k: data_uri(k)
    for k in ("ec2", "iamrole", "ssm", "ecr", "s3std", "s3dir", "gVpc", "gSubnet")
}

W, H = 960, 540
NODE = 52


def node(x, y, icon, label, sub=""):
    ix = x - NODE / 2
    sub_line = (
        f'<text x="{x}" y="{y + 84}" class="sub">{sub}</text>' if sub else ""
    )
    return f"""
  <g>
    <image x="{ix}" y="{y}" width="{NODE}" height="{NODE}" href="{ICONS[icon]}"/>
    <text x="{x}" y="{y + 70}" class="lbl">{label}</text>
    {sub_line}
  </g>"""


def arrow(x1, y1, x2, y2, label="", dashed=False, mid_dx=0, mid_dy=-6):
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
VPC_X, VPC_Y, VPC_W, VPC_H = 30, 60, 460, 420
SUB_X, SUB_Y, SUB_W, SUB_H = 60, 150, 400, 300

# EC2 + its instance profile (role), inside the subnet
EC2_X, EC2_Y = 160, 250
ROLE_X, ROLE_Y = 360, 250

# targets on the right (the four grants)
T_X = 760
DIR_Y, STD_Y, ECR_Y, SSM_Y = 80, 205, 330, 430

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

  <text x="24" y="34" class="title">Instance profile grants &#183; m7g.large in apse2-az1</text>

  <!-- VPC container -->
  <rect x="{VPC_X}" y="{VPC_Y}" width="{VPC_W}" height="{VPC_H}" rx="8" fill="none" stroke="#8C4FFF" stroke-width="2"/>
  <image x="{VPC_X + 8}" y="{VPC_Y + 8}" width="24" height="24" href="{ICONS['gVpc']}"/>
  <text x="{VPC_X + 40}" y="{VPC_Y + 20}" class="grp" fill="#8C4FFF">VPC</text>
  <text x="{VPC_X + 40}" y="{VPC_Y + 34}" class="grpsub">10.87.0.0/16</text>

  <!-- Public subnet container -->
  <rect x="{SUB_X}" y="{SUB_Y}" width="{SUB_W}" height="{SUB_H}" rx="6" fill="#f2f8ea" stroke="#7AA116" stroke-width="2"/>
  <image x="{SUB_X + 8}" y="{SUB_Y + 8}" width="22" height="22" href="{ICONS['gSubnet']}"/>
  <text x="{SUB_X + 36}" y="{SUB_Y + 18}" class="grp" fill="#5c7a10">Public subnet</text>
  <text x="{SUB_X + 36}" y="{SUB_Y + 32}" class="grpsub">apse2-az1 &#183; harness :8080</text>

{node(EC2_X, EC2_Y, "ec2", "EC2 m7g.large", "arm64 &#183; user-data")}
{node(ROLE_X, ROLE_Y, "iamrole", "Instance profile", "IAM role")}

  <!-- grant targets -->
{node(T_X, DIR_Y, "s3dir", "Directory bucket", "Express One Zone")}
{node(T_X, STD_Y, "s3std", "Standard bucket", "bakeoff baseline")}
{node(T_X, ECR_Y, "ecr", "ECR", "harness image")}
{node(T_X, SSM_Y, "ssm", "Session Manager", "no inbound SSH")}

  <!-- EC2 assumes the role -->
{arrow(EC2_X + 30, EC2_Y + 26, ROLE_X - 30, ROLE_Y + 26, "assumes", mid_dy=-8)}

  <!-- role grants: arrows from the role edge to each target's left side -->
{arrow(ROLE_X + 26, ROLE_Y + 4, T_X - 34, DIR_Y + 28, "")}
{arrow(ROLE_X + 30, ROLE_Y + 22, T_X - 34, STD_Y + 26, "")}
{arrow(ROLE_X + 30, ROLE_Y + 38, T_X - 34, ECR_Y + 26, "", dashed=True)}
{arrow(ROLE_X + 26, ROLE_Y + 48, T_X - 34, SSM_Y + 26, "")}

  <!-- grant labels: centered in the open corridor between role and targets,
       each with a small white plate so lines never show through the text -->
  {"".join(
      f'<rect x="{lx - w/2}" y="{ly - 11}" width="{w}" height="16" rx="3" fill="#ffffff" opacity="0.92"/>'
      f'<text x="{lx}" y="{ly}" class="edgelbl">{txt}</text>'
      for lx, ly, w, txt in [
          (600, 165, 150, "s3express:CreateSession"),
          (600, 232, 96, "s3:Get / Put / List"),
          (600, 306, 60, "ecr: pull"),
          (600, 372, 176, "AmazonSSMManagedInstanceCore"),
      ]
  )}

  <!-- legend -->
  <line x1="{VPC_X}" y1="{H - 12}" x2="{VPC_X + 30}" y2="{H - 12}" class="edge"/>
  <text x="{VPC_X + 36}" y="{H - 8}" class="legend">IAM grant</text>
  <line x1="{VPC_X + 150}" y1="{H - 12}" x2="{VPC_X + 180}" y2="{H - 12}" class="edge" stroke-dasharray="6 5"/>
  <text x="{VPC_X + 186}" y="{H - 8}" class="legend">image pull (user-data at boot)</text>
</svg>
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(svg, encoding="utf-8")
print(f"wrote {OUT} ({len(svg)} bytes)")
