# Agent Context

Guided AWS CLI walkthrough for **Amazon S3 Express One Zone shared hot lookup** — a
same-AZ small-object bakeoff against S3 Standard with a built-in harness dashboard —
published as an Astro Starlight site.

## Read these first

Kiro loads `.kiro/steering/` automatically; other agents should read them directly.

| File                                  | When it applies              | What it covers                                   |
| --- | --- | --- |
| `.kiro/steering/product.md`           | always                       | Story, scope, non-goals, visual bias             |
| `.kiro/steering/tech.md`              | always                       | Stack, commands, lab tooling                     |
| `.kiro/steering/structure.md`         | always                       | Layout, page rules, naming                       |
| `.kiro/steering/aws-source-lock.md`   | always                       | **Citation rules, verified facts, open TBDs**    |
| `.kiro/steering/docs-pattern.md`      | `src/content/docs/**`        | Page template, MDX indentation traps             |
| `.kiro/steering/editor-tooling.md`    | `src/content/docs/**`        | **What the automated gates reject**              |
| `.kiro/steering/markdown-tables.md`   | `src/content/docs/**`        | HTML tables when components are imported         |
| `.kiro/steering/glossary.md`          | `src/data/glossary*`         | Alphabetical order, term list                    |
| `.kiro/steering/lab-safety.md`        | `scripts/**`, install/prereq/cli pages | Profile `sandbox`, Region, CLI pins, teardown |
| `.kiro/steering/evidence-capture.md`  | manual (`#evidence-capture`) | Screenshot and diagram pass                      |

Lab CLI: AWS CLI **≥ 2.15.0** (latest fine); profile **`sandbox`**; Region
**`ap-southeast-2`**; Express AZ **`apse2-az1`**. Start readers at **Install tooling**.

## Non-negotiables

1. **Cite AWS behaviour.** Do not answer from recall — use the `aws-docs` MCP server and
   the source list in `aws-source-lock.md`. Unsourced claims do not ship.
2. **Never run AWS mutations.** Author the command; the operator runs it. The
   `guard-aws-mutations` hook blocks mutating AWS CLI and IaC commands from shell tools
   unless `S3X_LAB_ALLOW_AWS=1`.
3. **Mark unverified work.** Nothing is "verified" until the evidence pass runs it in an
   account.
4. **Prefer visuals.** Diagrams, tables, and short numbered steps over paragraphs.
5. **Dedicated VPC.** This lab creates its own VPC. Do not attach to an existing shared VPC.

## Facts that trip people up

- Sydney Express One Zone has **one** AZ ID: `apse2-az1`. Bucket names use the AZ **ID**
  (`…--apse2-az1--x-s3`), not `ap-southeast-2a`.
- Map AZ ID → AZ name per account with `describe-availability-zones --zone-ids`.
- Zonal object APIs are authorized via **`s3express:CreateSession`**, not classic
  `s3:GetObject` on the directory bucket.
- Need **two** gateway VPC endpoints: `….s3` (Standard) and `….s3express` (directory).
- Compute must sit in the **same AZ** as the directory bucket or the latency story is gone.

The complete list, with sources, is in `.kiro/steering/aws-source-lock.md`.

## Plan of record

`.kiro/specs/s3-express-hot-lookup-walkthrough/` holds `requirements.md`, `design.md`, and
`tasks.md`. Work the phases in order; the evidence pass is deliberately last.

## Validation

```bash
node scripts/check-placeholders.mjs
node scripts/check-asides.mjs
node scripts/check-references.mjs
```

After scaffolding, the same set runs as `npm run validate`, and `npm run build` is the CI
gate. Use `SKIP_LINK_CHECK=1` offline.

## Diagrams and icons

- AWS service icons — <https://jajera.github.io/aws-icons/>
- Generic architecture icons — <https://jajera.github.io/arch-icons/>
- Mermaid scratchpad — <https://jajera.github.io/mermaid-diagram-editor/>
