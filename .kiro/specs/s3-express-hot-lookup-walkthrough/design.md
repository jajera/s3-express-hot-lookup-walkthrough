# Design — S3 Express hot lookup walkthrough

For the full system view (network, IAM, harness, lifecycle, failure domains),
see [`architecture.md`](../../../architecture.md) at the repo root.

## Architecture (summary)

```text
Operator laptop (sandbox)
        │ demo.sh
        ▼
Dedicated VPC 10.87.0.0/16
  ├─ public subnet in AZ(apse2-az1)
  ├─ IGW + route table
  ├─ Gateway EP com.amazonaws.ap-southeast-2.s3
  ├─ Gateway EP com.amazonaws.ap-southeast-2.s3express
  └─ EC2 m7g.large
        └─ Docker harness :8080
              ├─ GET loop → Standard bucket
              └─ GET loop → Directory bucket (--apse2-az1--x-s3)
```

## Auth

- Instance role: Standard bucket object/list actions; `s3express:CreateSession`
  scoped to directory bucket ARN
  `arn:aws:s3express:region:account:bucket/name--az--x-s3`.

## Observability

One process, one page. No Prometheus. `/api/stats` JSON + `dash.html`.

## Safety

`S3X_LAB_ALLOW_AWS=1` required for mutations when the Kiro guard is active.
Agents author commands; operators run them.
