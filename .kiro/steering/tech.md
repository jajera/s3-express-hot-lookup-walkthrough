---
inclusion: always
---

# Tech

## Documentation site

Astro + `@astrojs/starlight`.

- Node 22 (pin in `.nvmrc`)
- MDX content under `src/content/docs/`
- Sidebar defined in `astro.config.mjs` — never encode order in filenames
- `astro-mermaid` for flow and sequence diagrams
- `starlight-image-zoom` so screenshots stay readable inline
- `starlight-base-path` so root-relative MDX links honour Astro `base`
- GitHub Pages deploy via the `actionsforge` reusable workflows
- Until `s3-express-hot-lookup-walkthrough.johna.kiwi` DNS exists, `site` is
  `https://jajera.github.io` and `base` is `/s3-express-hot-lookup-walkthrough/`
  (no `public/CNAME`). Custom-domain cutover: DNS CNAME → `jajera.github.io`,
  restore `public/CNAME`, set `site` to the johna.kiwi URL and `base` to `/`.

## Commands

```bash
npm install
npm run dev       # local preview
npm run validate  # placeholder, aside, and source-lock gates
npm run test      # vitest over the validator scripts
npm run build     # og image + validate + astro build; the CI gate
```

The validators run standalone on Node with no dependencies, so they work before `npm install`:

```bash
node scripts/check-placeholders.mjs
node scripts/check-asides.mjs
SKIP_LINK_CHECK=1 node scripts/check-references.mjs
```

## Lab tooling

- `scripts/image.sh` — durable ECR + CodeBuild (`up|build|status|down`)
- `scripts/demo.sh` — ephemeral lab (`up|status|seed|harness|dash|down`)
- `harness/` — Dockerized bakeoff + built-in dashboard (built in CodeBuild, pulled on EC2)
- State: `.lab-state.json`, `.image-state.json`, work dir `.lab/` (all gitignored)
- Profile default: `sandbox`; Region default: `ap-southeast-2` (see `.envrc`)
