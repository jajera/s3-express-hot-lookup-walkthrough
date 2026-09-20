---
inclusion: fileMatch
fileMatchPattern: "src/data/glossary*"
---

# Glossary conventions

- Lives in `src/data/glossary.ts` as `Record<string, GlossaryEntry>`.
  `GlossaryEntry` is a string, or `{ definition, url?, urlLabel? }`.
- Keys are lowercase kebab-case, sorted **alphabetically ascending**. Re-sort after adding.
- Definitions are one or two sentences, starting with the expanded form.
- Use walkthrough-specific context where it helps.

## Terms this walkthrough needs

`az-id`, `create-session`, `directory-bucket`, `gateway-endpoint`, `harness`, `s3-express`,
`shared-hot-lookup`.

## Usage

```mdx
import Tooltip from "@/components/Tooltip.astro";

<Tooltip term="directory-bucket" />
<Tooltip term="s3-express" label="S3 Express One Zone" />
```

Add a term when it appears on more than one page, or when it has a meaning here that a first-time
reader would not guess. Do not inline definitions in page bodies.
