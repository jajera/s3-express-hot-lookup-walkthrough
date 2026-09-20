---
inclusion: always
---

# Product

`s3-express-hot-lookup-walkthrough` publishes a guided CLI walkthrough for **Amazon S3 Express One
Zone shared hot lookup** — co-locate a directory bucket with compute in `apse2-az1`, bake off
continuous GETs against a Standard general-purpose bucket, and tear everything down.

## The story

Stand up a dedicated VPC with both S3 gateway endpoints, create Express + Standard buckets, launch
an `m7g.large` in the Express AZ, seed shared hot keys, run a harness dashboard on `:8080`, read
p50/p90 ratios, then delete the stack.

```text
Operator laptop (AWS CLI + demo.sh)
        │
        ▼
Dedicated VPC 10.87.0.0/16  (public subnet → apse2-az1)
  gateway endpoints: s3 + s3express
        │
        ▼
EC2 m7g.large  ──GET──►  directory bucket (Express One Zone)
        │                s3x-hotlookup-${LAB_SUFFIX}--apse2-az1--x-s3
        └──GET──►  Standard bucket (bakeoff baseline)
        │
        ▼
Harness dashboard :8080  (p50 / p90 ratios)
```

## Audience

Engineers who already know S3 basics and want to see Express One Zone latency behaviour for a
shared hot-lookup pattern without building a full application.

## Shape of the lab

- **Guided AWS CLI**, wrapped by `scripts/demo.sh`
  (`up` / `status` / `seed` / `harness` / `dash` / `down`).
- Profile **`sandbox`**, Region **`ap-southeast-2`**, Express AZ ID **`apse2-az1`** only.
- Mutation guard: `S3X_LAB_ALLOW_AWS=1`.
- Target length: under an hour once tooling is ready (evidence pass TBD).

## In scope

- Dedicated VPC, dual gateway endpoints, Standard + directory buckets, IAM/instance profile,
  `m7g.large`, seed, harness dashboard, teardown.
- Reference pages for commands, costs/limits, troubleshooting, cleanup checklist.

## Out of scope (v1)

- CDK, Terraform, or CloudFormation as the primary path.
- Multi-AZ Express (Sydney has one Express AZ for this lab).
- Mountpoint, EMR, or analytics pipelines as the primary demo.
- Production capacity planning or hardcoding prices.

## Visual bias

Prefer diagrams, tables, and short numbered steps over prose. Text diagrams (including Mermaid)
are acceptable now; real screenshots land in the evidence pass — see `#evidence-capture`.
