# S3 Express Hot Lookup Walkthrough

Hands-on CLI lab for **Amazon S3 Express One Zone** shared hot lookup in Asia Pacific
(Sydney): dedicated VPC, directory bucket in `apse2-az1`, same-AZ EC2 bakeoff against
S3 Standard, and a built-in harness dashboard pulled from ECR.

## Quick start (docs site)

```bash
npm install
npm run dev
```

## Lab (AWS)

```bash
export AWS_PROFILE=sandbox
export AWS_REGION=ap-southeast-2
# operators only — agents must not set this unprompted:
# export S3X_LAB_ALLOW_AWS=1

./scripts/image.sh up
./scripts/image.sh build
./scripts/demo.sh up
./scripts/demo.sh status
./scripts/demo.sh dash
./scripts/demo.sh down
./scripts/image.sh down   # required to remove ECR / CodeBuild / source bucket
```

See [architecture.md](./architecture.md) for the system design, and
`src/content/docs/` for the guided operator path.

## License

MIT — see [LICENSE](./LICENSE).
