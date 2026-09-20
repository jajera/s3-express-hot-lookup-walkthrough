# Requirements — S3 Express hot lookup walkthrough

## Goal

Publish a CLI-first Starlight walkthrough that proves S3 Express One Zone as a
**shared hot lookup** tier in `ap-southeast-2` / `apse2-az1`, with a same-AZ
GET bakeoff against S3 Standard and a built-in harness dashboard.

## Functional

1. Reader installs AWS CLI (≥ 2.15.0; latest fine) and jq.
2. Lab uses profile `sandbox` and Region `ap-southeast-2`.
3. `demo.sh up` creates a **dedicated** VPC (not shared), both S3 gateway
   endpoints (`s3` + `s3express`), Standard + directory buckets, IAM,
   `m7g.large` in the AZ mapped from `apse2-az1`, seeds keys, starts harness.
4. Dashboard on `:8080` shows live Express vs Standard latency percentiles.
5. `demo.sh down` tears everything down after LAB_SUFFIX confirmation.

## Non-goals (v1)

- Terraform / CDK
- Mountpoint for S3 (`--cache-xz`) — optional later
- Prometheus / CloudWatch dashboards
- Multi-AZ or multi-Region Express

## Success

- `npm run build` passes
- Evidence pass (operator) completes `up → dash → down` once in a real account
