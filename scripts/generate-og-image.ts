/**
 * Regenerates public/og-image.svg and public/og-image.png.
 *
 * Embeds official AWS Architecture Icons (jajera/aws-icons) plus the Docker mark
 * (jajera/arch-icons) as data URIs. Icons are read from .lab/icons/ — fetch them
 * once if missing (see ensureIcons below).
 *
 *   npm run generate:og-image
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import sharp from "sharp";

const root = process.cwd();
const iconDir = join(root, ".lab/icons");
const svgOut = join(root, "public/og-image.svg");
const pngOut = join(root, "public/og-image.png");

const ICON_SOURCES: { file: string; url: string }[] = [
  {
    file: "gVpc.svg",
    url: "https://raw.githubusercontent.com/jajera/aws-icons/main/icons/group/networking/Virtual-private-cloud-VPC_32.svg",
  },
  {
    file: "ec2.svg",
    url: "https://raw.githubusercontent.com/jajera/aws-icons/main/icons/resource/compute/Res_Amazon-EC2_Instance_48.svg",
  },
  {
    file: "iamrole.svg",
    url: "https://raw.githubusercontent.com/jajera/aws-icons/main/icons/resource/security/Res_AWS-Identity-Access-Management_Role_48.svg",
  },
  {
    file: "docker.svg",
    url: "https://raw.githubusercontent.com/jajera/arch-icons/main/icons/docker/docker-mark-white.svg",
  },
  {
    file: "ecr.svg",
    url: "https://raw.githubusercontent.com/jajera/aws-icons/main/icons/service/containers/Arch_Amazon-Elastic-Container-Registry_64.svg",
  },
  {
    file: "codebuild.svg",
    url: "https://raw.githubusercontent.com/jajera/aws-icons/main/icons/service/developer/Arch_AWS-CodeBuild_64.svg",
  },
  {
    file: "s3std.svg",
    url: "https://raw.githubusercontent.com/jajera/aws-icons/main/icons/resource/storage/Res_Amazon-Simple-Storage-Service_S3-Standard_48.svg",
  },
  {
    file: "s3dir.svg",
    url: "https://raw.githubusercontent.com/jajera/aws-icons/main/icons/resource/storage/Res_Amazon-Simple-Storage-Service_Directory-bucket_48.svg",
  },
];

async function ensureIcons() {
  mkdirSync(iconDir, { recursive: true });
  for (const { file, url } of ICON_SOURCES) {
    const dest = join(iconDir, file);
    if (existsSync(dest) && readFileSync(dest).byteLength > 100) continue;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to fetch ${url}: ${res.status}`);
    writeFileSync(dest, Buffer.from(await res.arrayBuffer()));
    console.log(`Fetched ${file}`);
  }
}

function dataUri(file: string): string {
  const raw = readFileSync(join(iconDir, file));
  return `data:image/svg+xml;base64,${raw.toString("base64")}`;
}

type Tile = { file: string; label: string; pad?: boolean };

const TILES: Tile[] = [
  { file: "gVpc.svg", label: "VPC" },
  { file: "ec2.svg", label: "EC2" },
  { file: "iamrole.svg", label: "IAM" },
  { file: "docker.svg", label: "Docker", pad: true },
  { file: "ecr.svg", label: "ECR" },
  { file: "codebuild.svg", label: "CodeBuild" },
  { file: "s3std.svg", label: "S3 Standard" },
  { file: "s3dir.svg", label: "S3 Express" },
];

await ensureIcons();

const uris = Object.fromEntries(TILES.map((t) => [t.file, dataUri(t.file)]));

// 4×2 icon grid on the right
const gridX = 640;
const gridY = 150;
const cellW = 120;
const cellH = 140;
const iconSz = 56;

function tile(t: Tile, col: number, row: number): string {
  const cx = gridX + col * cellW + cellW / 2;
  const top = gridY + row * cellH;
  const ix = cx - iconSz / 2;
  // Docker white mark needs a dark chip so it reads on the panel
  const chip = t.pad
    ? `<rect x="${ix - 8}" y="${top - 8}" width="${iconSz + 16}" height="${iconSz + 16}" rx="12" fill="#0d2a32"/>`
    : "";
  return `
  <g>
    ${chip}
    <image x="${ix}" y="${top}" width="${iconSz}" height="${iconSz}" href="${uris[t.file]}"/>
    <text x="${cx}" y="${top + iconSz + 28}" text-anchor="middle" fill="#b7cdd4" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="16" font-weight="600">${t.label}</text>
  </g>`;
}

const tilesSvg = TILES.map((t, i) => tile(t, i % 4, Math.floor(i / 4))).join(
  "\n",
);

const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img">
  <defs>
    <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">
      <circle cx="1.5" cy="1.5" r="1" fill="#2dd4bf" fill-opacity="0.12"/>
    </pattern>
    <radialGradient id="glow" cx="18%" cy="0%" r="70%">
      <stop offset="0%" stop-color="#2dd4bf" stop-opacity="0.18"/>
      <stop offset="55%" stop-color="#071014" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0d2a32" stop-opacity="0.85"/>
      <stop offset="100%" stop-color="#071014" stop-opacity="0.4"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="#071014"/>
  <rect width="1200" height="630" fill="url(#dots)"/>
  <rect width="1200" height="630" fill="url(#glow)"/>

  <text x="72" y="108" fill="#2dd4bf" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="24" font-weight="700" letter-spacing="0.08em">S3 EXPRESS ONE ZONE</text>
  <text x="72" y="200" fill="#eef8fa" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="52" font-weight="800">Shared hot lookup</text>
  <text x="72" y="268" fill="#eef8fa" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="52" font-weight="800">in one AZ</text>
  <text x="72" y="340" fill="#b7cdd4" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="24">Same-AZ bakeoff · Express vs Standard</text>

  <rect x="72" y="390" width="220" height="48" rx="24" fill="#2dd4bf"/>
  <text x="182" y="421" text-anchor="middle" fill="#04222a" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="20" font-weight="700">Start the lab</text>

  <text x="72" y="560" fill="#5a7a86" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="18">s3-express-hot-lookup-walkthrough.johna.kiwi</text>

  <!-- Service icons used in the lab -->
  <rect x="610" y="100" width="530" height="430" rx="20" fill="url(#panel)" stroke="#1a4a55" stroke-width="1.5"/>
  <text x="875" y="136" text-anchor="middle" fill="#2dd4bf" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="15" font-weight="700" letter-spacing="0.06em">LAB STACK</text>
${tilesSvg}
</svg>
`;

writeFileSync(svgOut, svg);
await sharp(Buffer.from(svg)).png().toFile(pngOut);
console.log(`Wrote ${svgOut}`);
console.log(`Wrote ${pngOut}`);
