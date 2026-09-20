---
inclusion: fileMatch
fileMatchPattern: ["scripts/**", "**/demo.sh", "**/image.sh", "src/content/docs/cli/**", "src/content/docs/install-tooling.mdx", "src/content/docs/prerequisites.mdx"]
---

# Lab safety

This lab creates billable AWS resources. These rules apply to `scripts/demo.sh` and to every CLI
page that tells a reader to run something.

## Never run AWS mutations unprompted

The agent does not create, update, or delete AWS resources on its own. Author the command, show
it, and let the operator run it. The `guard-aws-mutations` hook blocks accidental execution.

## Lab conventions

| Convention  | Value |
| --- | --- |
| Profile     | `sandbox` (`AWS_PROFILE=sandbox`) |
| Region      | `ap-southeast-2` |
| Express AZ  | `apse2-az1` only |
| AWS CLI     | Minimum **2.15.0** (latest v2 recommended) |
| Lab suffix  | `LAB_SUFFIX` — short unique token; `demo.sh up` defaults to `$(date +%Y%m%d%H%M%S)` when unset |
| Name prefix | `s3x-hotlookup-${LAB_SUFFIX}-…` |
| Directory bucket | `s3x-hotlookup-${LAB_SUFFIX}--apse2-az1--x-s3` |
| VPC         | Dedicated `10.87.0.0/16` — do not share an existing VPC |
| Endpoints   | Gateway `com.amazonaws.ap-southeast-2.s3` **and** `com.amazonaws.ap-southeast-2.s3express` |
| Instance    | `m7g.large` (Graviton/arm64) in the AZ mapped to `apse2-az1`; override with `INSTANCE_TYPE` |
| Tags        | `Project=s3-express-hot-lookup-walkthrough` |
| Mutation guard | `S3X_LAB_ALLOW_AWS=1` |
| Local dir   | `.lab/` (gitignored) |
| Lab state   | `.lab-state.json` (gitignored) — ARNs and suffix from `demo.sh` |
| Image state | `.image-state.json` (gitignored) — ECR/CodeBuild from `image.sh` |
| ECR repo    | `s3x-hotlookup-harness` (durable; not removed by `demo.sh down`) |

Every created resource carries the prefix and the tag so that a stray resource is greppable and
`down` can be trusted.

## `image.sh` contract (durable)

| Subcommand | Does |
| --- | --- |
| `up`       | ECR repo, CodeBuild source bucket, CodeBuild IAM role, CodeBuild project |
| `build`    | Zip `harness/`, upload, start CodeBuild, wait for SUCCEEDED, push image |
| `status`   | Recent images and builds. Read-only. |
| `down`     | Deletes image pipeline after typing the ECR repo name |

## `demo.sh` contract (ephemeral lab)

| Subcommand | Does |
| --- | --- |
| `up`       | Requires an existing ECR image. VPC, dual gateway endpoints, buckets, IAM, `m7g.large` (pulls harness). |
| `status`   | Instance, buckets, harness readiness. Read-only. |
| `seed`     | Puts identical hot keys into Express and Standard. |
| `harness`  | Prints how to rebuild via CodeBuild / re-pull (does not build on EC2). |
| `dash`     | Prints the public dashboard URL. Read-only. |
| `port-forward` | SSM tunnel of harness `:8080` to localhost (Session Manager plugin required). |
| `down`     | Ordered lab teardown after explicit `LAB_SUFFIX` confirmation. Leaves ECR/CodeBuild alone. |

Rules for the script:

- Echo each AWS CLI command before running it — the script teaches, it does not hide.
- `set -euo pipefail`.
- Fail fast if `AWS_REGION` or `AWS_PROFILE` is unset; never fall back to an implicit account.
  Documented values: `AWS_PROFILE=sandbox`, `AWS_REGION=ap-southeast-2`.
- Mutating AWS CLI from agent shell tools is blocked by the Kiro `guard-aws-mutations` hook
  unless `S3X_LAB_ALLOW_AWS=1`. Operators set that deliberately; the wrappers do not enforce it
  themselves.
- `down` stops the harness and terminates EC2 before deleting buckets; empties buckets before
  delete; removes endpoints before the VPC.
- `status`, `dash`, and `port-forward` must be safe to run at any time.
- Never use `--force`, `rm -rf`, or a wildcard delete that could reach outside the lab prefix.

## Cost callouts in content

Every page that creates a resource states that it is billable, and links
[S3 pricing](https://aws.amazon.com/s3/pricing/) and/or
[EC2 On-Demand pricing](https://aws.amazon.com/ec2/pricing/on-demand/) instead of hardcoding a
rate. The teardown page and cleanup checklist cover the lab (instance, buckets, VPC, IAM) and
the image stack (ECR, CodeBuild, source bucket).

## ARN placeholders

In fenced documentation samples, use account **`123456789012`** whenever an ARN is shown.
