---
inclusion: always
---

# AWS source lock

Model training data about S3 Express One Zone and directory buckets can be incomplete or stale,
so **every AWS behavioural claim in this repository must trace to a source below**. If a claim is
not in a source and not verified in an account, it does not go in the walkthrough.

## Canonical sources

| Topic | Source |
| --- | --- |
| High-performance directory buckets | https://docs.aws.amazon.com/AmazonS3/latest/userguide/directory-bucket-high-performance.html |
| Create directory buckets | https://docs.aws.amazon.com/AmazonS3/latest/userguide/directory-bucket-create.html |
| Directory bucket AZ networking | https://docs.aws.amazon.com/AmazonS3/latest/userguide/directory-bucket-az-networking.html |
| Authenticating and authorizing | https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-express-authenticating-authorizing.html |
| IAM for S3 Express | https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-express-security-iam.html |
| Regions and Zones | https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-express-Regions-and-Zones.html |
| Differences vs general purpose | https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-express-differences.html |
| Endpoints for directory buckets (AZ) | https://docs.aws.amazon.com/AmazonS3/latest/userguide/endpoint-directory-buckets-AZ.html |
| S3 Express One Zone product | https://aws.amazon.com/s3/storage-classes/express-one-zone/ |
| Express AZ-loss / Reliability (Solutions guidance) | https://docs.aws.amazon.com/solutions/writing-high-transaction-workloads-on-amazon-s3-express-one-zone/ |
| Optimizing Express performance (co-locate) | https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-express-optimizing-performance-design-patterns.html |
| Amazon S3 FAQs (Express availability) | https://aws.amazon.com/s3/faqs/ |
| S3 pricing | https://aws.amazon.com/s3/pricing/ |
| EC2 On-Demand pricing | https://aws.amazon.com/ec2/pricing/on-demand/ |
| Session Manager instance profile | https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-getting-started-instance-profile.html |
| Session Manager start a session | https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-sessions-start.html |
| Session Manager plugin install | https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html |
| Using tags with directory buckets | https://docs.aws.amazon.com/AmazonS3/latest/userguide/directory-buckets-tagging.html |
| AWS CLI install | https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html |
| AWS CLI past releases | https://docs.aws.amazon.com/cli/latest/userguide/getting-started-version.html |
| AWS CLI install script | https://awscli.amazonaws.com/v2/install.sh |
| AWS CLI linux x86_64 (latest) | https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip |
| Amazon ECR overview | https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html |
| ECR getting started (CLI) | https://docs.aws.amazon.com/AmazonECR/latest/userguide/getting-started-cli.html |
| CodeBuild overview | https://docs.aws.amazon.com/codebuild/latest/userguide/welcome.html |
| CodeBuild buildspec reference | https://docs.aws.amazon.com/codebuild/latest/userguide/build-spec-ref.html |
| Create directory buckets with tags | https://docs.aws.amazon.com/AmazonS3/latest/userguide/directory-bucket-create-tag.html |
| Using tags with S3 directory buckets | https://docs.aws.amazon.com/AmazonS3/latest/userguide/directory-buckets-tagging.html |

Use the `aws-docs` MCP server to re-read these pages rather than recalling them.

## Verified facts (safe to state from docs)

1. Directory bucket names follow **`bucket-base-name--zone-id--x-s3`**.
2. Create uses **Availability Zone** location type with the **AZ ID** (for example
   `apse2-az1`), not the account-local AZ name.
3. Zonal (object-level) operations use session-based auth via **`s3express:CreateSession`**.
4. Gateway VPC endpoint service for Express is **`com.amazonaws.<region>.s3express`** (lab:
   `com.amazonaws.ap-southeast-2.s3express`), in addition to the regional S3 gateway endpoint.
5. Sydney (`ap-southeast-2`) Express AZ ID used by this lab is **`apse2-az1`** only.
6. S3 Express One Zone stores data redundantly **within a single Availability Zone** (by
   design for latency). Designed for **99.95% availability within that AZ** (S3 SLA).
7. In the unlikely case of loss or damage to all or part of an Availability Zone, data in the
   Express One Zone storage class **may be lost** — device-level redundancy inside the AZ is
   not Region-level durability (AWS Solutions guidance, Reliability pillar).
8. AWS CLI for this lab: minimum **2.15.0**; latest v2 is fine.
9. Directory buckets **support tagging** via the **`s3express`** path
   (**`s3express:TagResource`** / S3 Control `tag-resource`), not classic
   `s3:PutBucketTagging` / `GetBucketTagging`. Tags can be applied **at create time** or
   **after create** (this lab tags post-create with `aws s3control tag-resource` on the
   `s3express` bucket ARN).

## Lab evidence — verified

Verified in `ap-southeast-2` with profile `sandbox` (lab suffix `20260920120148`):

- `./scripts/image.sh up` — ECR `s3x-hotlookup-harness`, CodeBuild project, source bucket,
  role `s3x-hotlookup-codebuild`.
- `./scripts/image.sh build` — CodeBuild `SUCCEEDED`; image tags `c3cad1d` and `latest` pushed
  (~40 s in this run).
- Directory bucket **tagging confirmed** in-account via S3 Control `tag-resource` on the
  `s3express` ARN (verified fact #9).
- End-to-end `./scripts/demo.sh up` — dedicated VPC, dual gateway endpoints (`s3` + `s3express`),
  Standard + directory buckets, `m7g.large` in the AZ mapped from `apse2-az1`, harness pull from
  ECR, seed, dashboard on `:8080`.
- Bakeoff shape (rolling window; **cite the ratio, not fixed ms**): Express p50 ≈ 6 ms, Standard
  p50 ≈ 25 ms, `standard_over_express_p50` ≈ **4.15** with zero errors after warm-up.
- `./scripts/demo.sh down` — terminate EC2, delete both buckets, endpoints, subnet/RT/IGW/VPC,
  IAM role + instance profile; `.lab-state.json` removed.
- `./scripts/image.sh down` — ECR repo, CodeBuild project, source bucket, CodeBuild role removed;
  `.image-state.json` removed. (Separate from `demo.sh down`; documented on Tear down.)

## Known trap: stale guidance

| Stale claim | Correct |
| --- | --- |
| “Use AZ name `ap-southeast-2a` in the directory bucket name” | Use AZ **ID** `apse2-az1` |
| “Only the regional S3 endpoint is required” | Also need `…s3express` for directory buckets |
| “SigV4 alone is enough for zonal object ops” | CreateSession for zonal access |
| “Express is multi-AZ durable like Standard” | Single-AZ storage class |
| “Docker must be on the laptop” | Harness runs on lab EC2 |
| “Directory buckets can’t be tagged (`GetBucketTagging` → `MethodNotAllowed`)” | Use `s3express:TagResource` / `s3control tag-resource`; classic `s3:*BucketTagging` still does not apply |

## Unresolved — must not be asserted

- Exact p50/p90 bakeoff ratios as a **product claim** — this account saw ~4× at p50; other
  accounts/times will differ. Cite ratio shape only.
- Current per-GB / per-request / On-Demand hourly prices — link pricing pages only.

## Rules

- Cite the source page for every behavioural claim; do not paraphrase from memory.
- Copy CLI examples from the AWS pages and change only names, ARNs, and Region.
- In fenced samples use placeholder account **`123456789012`** when showing ARNs.
- Label anything not yet run in an account as unverified. Only the evidence pass may mark a step
  “verified”.
- Never invent flags, metric names, IAM actions, or console labels.
