# Tasks — S3 Express hot lookup walkthrough

## Phase 0 — Scaffold (this pass)

- [x] Copy Starlight shell from kinesis sibling
- [x] Retarget package/astro/AGENTS/steering
- [x] `harness/` container + built-in dash
- [x] `scripts/demo.sh` (dedicated VPC, dual gateway EPs, buckets, EC2, seed)
- [x] CLI + reference MDX pages
- [x] Source lock + validators green offline

## Phase 1 — Operator evidence (next)

- [x] `S3X_LAB_ALLOW_AWS=1 ./scripts/demo.sh up` with `sandbox` / `ap-southeast-2`
- [x] Confirm harness `/healthz` and dashboard ratio after bootstrap
- [x] Capture screenshots into `src/assets/`
- [x] `./scripts/demo.sh down` and cleanup checklist sweep
- [x] Mark verified facts in `aws-source-lock.md`

## Phase 2 — Polish

- [ ] draw.io architecture diagram
- [ ] Optional Mountpoint appendix (non-blocking)
- [ ] Custom domain cutover when DNS exists
