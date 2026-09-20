---
inclusion: always
---

# Structure

## Target layout

```plaintext
.github/
  workflows/             # actionsforge reusable workflows only
  dependabot.yml
.kiro/
  settings/mcp.json      # MCP servers (aws-docs enabled, aws-api disabled)
  steering/              # these files
  hooks/                 # guard rails and save-time checks
scripts/
  demo.sh                # up | status | seed | harness | dash | down
  image.sh               # up | build | status | down (ECR + CodeBuild)
  check-placeholders.mjs
  check-asides.mjs
  check-references.mjs
harness/                 # Dockerfile + buildspec.yml + bakeoff app
architecture.md          # detailed lab system design
tests/                   # vitest over the validators
src/content/docs/
  index.mdx              # splash + why Express for shared hot lookup
  install-tooling.mdx    # AWS CLI / jq — Docker on EC2 only
  prerequisites.mdx
  architecture.mdx       # what we build — before Walkthrough (official-icon SVG)
  cli/
    index.mdx            # reading order + demo.sh cheat sheet
    setup/image.mdx      # ECR + CodeBuild harness image
    setup/vpc.mdx
    setup/buckets.mdx
    setup/iam-and-ec2.mdx
    harness.mdx
    dashboard.mdx
    teardown.mdx
  guidance/
    where-express-fits.mdx   # single-AZ trade-offs after the bakeoff
  reference/
    commands.mdx
    costs-and-limits.mdx
    troubleshooting.mdx
    cleanup-checklist.mdx
src/data/glossary.ts
astro.config.mjs
```

## Page rules

- One job per page. Short lede, then the commands.
- Every page that makes an AWS behavioural claim ends with a `## References` section linking the
  AWS documentation page that states it. Every `cli/` and `reference/` page **must** end with
  `## References`.
- Reading order is VPC → buckets → IAM/EC2 → seed/harness → dashboard → teardown → guidance
  (Where Express fits).
- Internal links are root-relative (`/cli/harness/`). Until custom DNS exists, Astro `base` is
  `/s3-express-hot-lookup-walkthrough/` on GitHub Pages.

## Naming in the lab

- Resource name prefix: `s3x-hotlookup-${LAB_SUFFIX}-…`
- Directory bucket: `s3x-hotlookup-${LAB_SUFFIX}--apse2-az1--x-s3`
- Tag everything `Project=s3-express-hot-lookup-walkthrough`
- See `.kiro/steering/lab-safety.md` for the exact conventions
