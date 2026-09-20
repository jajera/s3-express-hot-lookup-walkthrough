#!/usr/bin/env bash
# Guided lab orchestrator for S3 Express One Zone shared hot lookup.
#
# Echoes every AWS CLI command before running it. Creates nothing unless the
# operator runs a mutating subcommand. See .kiro/steering/lab-safety.md.
#
# Usage:
#   ./scripts/demo.sh up|status|seed|harness|dash|port-forward|down
#
# Prerequisite (durable image pipeline, once per account/Region):
#   ./scripts/image.sh up && ./scripts/image.sh build
#
# Required env:
#   AWS_REGION   — lab Region (documented default: ap-southeast-2)
#   AWS_PROFILE  — named profile (documented: sandbox); never fall back to an implicit account
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_FILE="${ROOT}/.lab-state.json"
IMAGE_STATE_FILE="${ROOT}/.image-state.json"
WORK_DIR="${ROOT}/.lab"
TAG_KEY="Project"
TAG_VALUE="s3-express-hot-lookup-walkthrough"
NAME_PREFIX="s3x-hotlookup"
ECR_REPO_NAME="s3x-hotlookup-harness"
DEFAULT_REGION="ap-southeast-2"
EXPRESS_AZ_ID="apse2-az1"
VPC_CIDR="10.87.0.0/16"
SUBNET_CIDR="10.87.1.0/24"
INSTANCE_TYPE="${INSTANCE_TYPE:-m7g.large}"
OBJECT_COUNT="${OBJECT_COUNT:-64}"
OBJECT_SIZE_BYTES="${OBJECT_SIZE_BYTES:-16384}"
OBJECT_PREFIX="${OBJECT_PREFIX:-hot/}"
HARNESS_PORT="${HARNESS_PORT:-8080}"
AWS_CLI_MIN_VERSION="2.15.0"

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

usage() {
  cat <<'EOF'
Usage: ./scripts/demo.sh <command>

Commands:
  up         Create dedicated VPC, gateway endpoints, buckets, IAM, EC2, seed; pull harness from ECR
  status     Show lab resources and harness reachability (read-only)
  seed       Re-upload the fixed hot-key set to both buckets
  harness    Print how to rebuild the ECR image and re-pull on the instance
  dash         Print the public dashboard URL (read-only)
  port-forward SSM port-forward harness :8080 to localhost (needs Session Manager plugin)
  down         Tear down lab resources after confirmation (does not delete ECR/CodeBuild)

Prerequisite:
  ./scripts/image.sh up && ./scripts/image.sh build

Required environment:
  AWS_REGION   Lab Region (documented default: ap-southeast-2)
  AWS_PROFILE  Named AWS CLI profile (documented: sandbox)

AWS CLI:
  Minimum  2.15.0 (latest v2 recommended)

Optional:
  LAB_SUFFIX              Short unique token in every resource name
                          (default on up: $(date +%Y%m%d%H%M%S); stored in .lab-state.json)
  HARNESS_IMAGE_TAG       ECR tag to pull (default: latest, or tag from .image-state.json)
  INSTANCE_TYPE           EC2 type (default: m7g.large)
  OBJECT_COUNT            Seed/harness key count (default: 64)
  OBJECT_SIZE_BYTES       Object size (default: 16384)
  HARNESS_PORT            Dashboard port (default: 8080)
  LOCAL_PORT              Local port for port-forward (default: same as HARNESS_PORT)
  DASH_CIDR               Ingress CIDR for port 8080 (default: 0.0.0.0/0 — lab only)
  S3X_LAB_ALLOW_AWS=1     Required for mutating subcommands when the Kiro guard is active
EOF
}

version_ge() {
  printf '%s\n%s\n' "$2" "$1" | sort -V | head -n1 | grep -qx "$2"
}

require_aws_cli_version() {
  command -v aws >/dev/null 2>&1 || die "aws CLI not found. See Install tooling — minimum ${AWS_CLI_MIN_VERSION}."
  local reported
  reported="$(aws --version 2>&1 | head -n1)"
  local ver
  ver="$(printf '%s' "$reported" | sed -n 's/^aws-cli\/\([0-9.]*\).*/\1/p')"
  [[ -n "$ver" ]] || die "Could not parse aws --version output: ${reported}"
  version_ge "$ver" "$AWS_CLI_MIN_VERSION" || die \
    "AWS CLI ${ver} is too old. Minimum is ${AWS_CLI_MIN_VERSION}. See Install tooling."
  printf 'aws cli: %s\n' "$reported" >&2
}

require_env() {
  [[ -n "${AWS_REGION:-}" ]] || die "AWS_REGION is unset. Example: export AWS_REGION=${DEFAULT_REGION}"
  [[ -n "${AWS_PROFILE:-}" ]] || die "AWS_PROFILE is unset. Example: export AWS_PROFILE=sandbox"
  require_aws_cli_version
}

run() {
  printf '+ %s\n' "$*" >&2
  "$@"
}

aws_cli() {
  run aws --profile "$AWS_PROFILE" --region "$AWS_REGION" "$@"
}

# EC2 describe calls that must stay regional
aws_ec2() {
  aws_cli ec2 "$@"
}

need_jq() {
  command -v jq >/dev/null 2>&1 || die "jq is required to read ${STATE_FILE}"
}

tag_spec() {
  # Usage: tag_spec ResourceType
  local rtype="$1"
  printf 'ResourceType=%s,Tags=[{Key=%s,Value=%s},{Key=Name,Value=%s}]' \
    "$rtype" "$TAG_KEY" "$TAG_VALUE" "${NAME_PREFIX}-${LAB_SUFFIX}"
}

write_state() {
  need_jq
  local tmp
  tmp="$(mktemp)"
  jq -n \
    --arg region "$AWS_REGION" \
    --arg profile "$AWS_PROFILE" \
    --arg suffix "$LAB_SUFFIX" \
    --arg account "$ACCOUNT_ID" \
    --arg az_id "$EXPRESS_AZ_ID" \
    --arg az_name "$AZ_NAME" \
    --arg vpc_id "$VPC_ID" \
    --arg subnet_id "$SUBNET_ID" \
    --arg igw_id "$IGW_ID" \
    --arg rtb_id "$RTB_ID" \
    --arg sg_id "$SG_ID" \
    --arg vpce_s3_id "${VPCE_S3_ID:-}" \
    --arg vpce_s3express_id "${VPCE_S3EXPRESS_ID:-}" \
    --arg role_name "$ROLE_NAME" \
    --arg instance_profile "$INSTANCE_PROFILE" \
    --arg standard_bucket "$STANDARD_BUCKET" \
    --arg express_bucket "$EXPRESS_BUCKET" \
    --arg instance_id "${INSTANCE_ID:-}" \
    --arg public_ip "${PUBLIC_IP:-}" \
    --arg instance_type "$INSTANCE_TYPE" \
    --arg harness_image "$HARNESS_IMAGE" \
    --arg harness_image_tag "$HARNESS_IMAGE_TAG" \
    --argjson object_count "$OBJECT_COUNT" \
    --argjson object_size "$OBJECT_SIZE_BYTES" \
    --arg object_prefix "$OBJECT_PREFIX" \
    --argjson harness_port "$HARNESS_PORT" \
    '{
      region: $region,
      profile: $profile,
      suffix: $suffix,
      accountId: $account,
      expressAzId: $az_id,
      azName: $az_name,
      vpcId: $vpc_id,
      subnetId: $subnet_id,
      igwId: $igw_id,
      routeTableId: $rtb_id,
      securityGroupId: $sg_id,
      vpcEndpointS3Id: $vpce_s3_id,
      vpcEndpointS3ExpressId: $vpce_s3express_id,
      roleName: $role_name,
      instanceProfile: $instance_profile,
      standardBucket: $standard_bucket,
      expressBucket: $express_bucket,
      instanceId: $instance_id,
      publicIp: $public_ip,
      instanceType: $instance_type,
      harnessImage: $harness_image,
      harnessImageTag: $harness_image_tag,
      objectCount: $object_count,
      objectSizeBytes: $object_size,
      objectPrefix: $object_prefix,
      harnessPort: $harness_port
    }' >"$tmp"
  mv "$tmp" "$STATE_FILE"
  printf 'Wrote %s\n' "$STATE_FILE"
}

load_state() {
  need_jq
  [[ -f "$STATE_FILE" ]] || die "No lab state at ${STATE_FILE}. Run: ./scripts/demo.sh up"
  AWS_REGION="$(jq -r '.region' "$STATE_FILE")"
  AWS_PROFILE="$(jq -r '.profile' "$STATE_FILE")"
  LAB_SUFFIX="$(jq -r '.suffix' "$STATE_FILE")"
  ACCOUNT_ID="$(jq -r '.accountId' "$STATE_FILE")"
  EXPRESS_AZ_ID="$(jq -r '.expressAzId' "$STATE_FILE")"
  AZ_NAME="$(jq -r '.azName' "$STATE_FILE")"
  VPC_ID="$(jq -r '.vpcId' "$STATE_FILE")"
  SUBNET_ID="$(jq -r '.subnetId' "$STATE_FILE")"
  IGW_ID="$(jq -r '.igwId' "$STATE_FILE")"
  RTB_ID="$(jq -r '.routeTableId' "$STATE_FILE")"
  SG_ID="$(jq -r '.securityGroupId' "$STATE_FILE")"
  VPCE_S3_ID="$(jq -r '.vpcEndpointS3Id // .vpcEndpointId // empty' "$STATE_FILE")"
  VPCE_S3EXPRESS_ID="$(jq -r '.vpcEndpointS3ExpressId // empty' "$STATE_FILE")"
  ROLE_NAME="$(jq -r '.roleName' "$STATE_FILE")"
  INSTANCE_PROFILE="$(jq -r '.instanceProfile' "$STATE_FILE")"
  STANDARD_BUCKET="$(jq -r '.standardBucket' "$STATE_FILE")"
  EXPRESS_BUCKET="$(jq -r '.expressBucket' "$STATE_FILE")"
  INSTANCE_ID="$(jq -r '.instanceId // empty' "$STATE_FILE")"
  PUBLIC_IP="$(jq -r '.publicIp // empty' "$STATE_FILE")"
  INSTANCE_TYPE="$(jq -r '.instanceType // "m7g.large"' "$STATE_FILE")"
  HARNESS_IMAGE="$(jq -r '.harnessImage // empty' "$STATE_FILE")"
  HARNESS_IMAGE_TAG="$(jq -r '.harnessImageTag // "latest"' "$STATE_FILE")"
  OBJECT_COUNT="$(jq -r '.objectCount // 64' "$STATE_FILE")"
  OBJECT_SIZE_BYTES="$(jq -r '.objectSizeBytes // 16384' "$STATE_FILE")"
  OBJECT_PREFIX="$(jq -r '.objectPrefix // "hot/"' "$STATE_FILE")"
  HARNESS_PORT="$(jq -r '.harnessPort // 8080' "$STATE_FILE")"
}

resolve_harness_image() {
  # Prefer explicit HARNESS_IMAGE; else ECR repo + tag from env / .image-state.json / latest.
  if [[ -n "${HARNESS_IMAGE:-}" ]]; then
    return 0
  fi
  ACCOUNT_ID="${ACCOUNT_ID:-$(aws_cli sts get-caller-identity --query Account --output text)}"
  if [[ -z "${HARNESS_IMAGE_TAG:-}" && -f "$IMAGE_STATE_FILE" ]]; then
    need_jq
    HARNESS_IMAGE_TAG="$(jq -r '.imageTag // "latest"' "$IMAGE_STATE_FILE")"
  fi
  HARNESS_IMAGE_TAG="${HARNESS_IMAGE_TAG:-latest}"
  HARNESS_IMAGE="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:${HARNESS_IMAGE_TAG}"

  if ! aws_cli ecr describe-repositories --repository-names "$ECR_REPO_NAME" >/dev/null 2>&1; then
    die "ECR repository ${ECR_REPO_NAME} not found. Run: ./scripts/image.sh up && ./scripts/image.sh build"
  fi
  # Confirm the tag (or :latest) exists.
  local tag_check="$HARNESS_IMAGE_TAG"
  if ! aws_cli ecr describe-images \
    --repository-name "$ECR_REPO_NAME" \
    --image-ids "imageTag=${tag_check}" >/dev/null 2>&1; then
    die "ECR image ${ECR_REPO_NAME}:${tag_check} not found. Run: ./scripts/image.sh build"
  fi
  printf 'Harness image: %s\n' "$HARNESS_IMAGE" >&2
}

resolve_az_name() {
  AZ_NAME="$(
    aws_ec2 describe-availability-zones \
      --zone-ids "$EXPRESS_AZ_ID" \
      --query 'AvailabilityZones[0].ZoneName' \
      --output text
  )"
  [[ -n "$AZ_NAME" && "$AZ_NAME" != "None" ]] || die \
    "Could not map AZ ID ${EXPRESS_AZ_ID} in ${AWS_REGION}. Is Express One Zone available in this account/Region?"
  printf 'AZ mapping: %s → %s\n' "$EXPRESS_AZ_ID" "$AZ_NAME" >&2
}

ensure_suffix() {
  if [[ -z "${LAB_SUFFIX:-}" ]]; then
    LAB_SUFFIX="$(date +%Y%m%d%H%M%S)"
    printf 'LAB_SUFFIX unset; using %s\n' "$LAB_SUFFIX" >&2
  fi
  # Directory bucket base name: [a-z0-9-] only, total name <= 63 with --az--x-s3 suffix.
  # --apse2-az1--x-s3 is 16 chars → base max 47.
  local base="${NAME_PREFIX}-${LAB_SUFFIX}"
  if ((${#base} > 47)); then
    die "LAB_SUFFIX too long for directory bucket naming (base '${base}' is ${#base} chars; max 47)"
  fi
}

seed_objects() {
  local tmpdir
  tmpdir="$(mktemp -d)"
  mkdir -p "${tmpdir}/hot"
  local i
  for ((i = 0; i < OBJECT_COUNT; i++)); do
    local key
    printf -v key '%sobj-%04d.bin' "$OBJECT_PREFIX" "$i"
    dd if=/dev/urandom of="${tmpdir}/${key}" bs="$OBJECT_SIZE_BYTES" count=1 status=none 2>/dev/null \
      || head -c "$OBJECT_SIZE_BYTES" /dev/urandom >"${tmpdir}/${key}"
  done
  printf 'Uploading %s objects (%s bytes) to Standard and Express…\n' "$OBJECT_COUNT" "$OBJECT_SIZE_BYTES" >&2
  # Standard: sync is fine for general-purpose buckets.
  aws_cli s3 sync "${tmpdir}/${OBJECT_PREFIX}" "s3://${STANDARD_BUCKET}/${OBJECT_PREFIX}" \
    --only-show-errors
  # Directory buckets reject `aws s3 sync`; use recursive cp instead.
  # https://aws.amazon.com/blogs/storage/unlocking-data-residency-use-cases-with-amazon-s3-in-aws-local-zones/
  aws_cli s3 cp "${tmpdir}/${OBJECT_PREFIX}" "s3://${EXPRESS_BUCKET}/${OBJECT_PREFIX}" \
    --recursive --only-show-errors
  rm -rf "$tmpdir"
}

build_user_data() {
  # shellcheck disable=SC2016
  cat <<EOF
#!/bin/bash
set -euo pipefail
exec > >(tee /var/log/s3x-harness-bootstrap.log) 2>&1

dnf -y update
dnf -y install docker
systemctl enable --now docker

REGION='${AWS_REGION}'
ACCOUNT_ID='${ACCOUNT_ID}'
STANDARD_BUCKET='${STANDARD_BUCKET}'
EXPRESS_BUCKET='${EXPRESS_BUCKET}'
HARNESS_PORT='${HARNESS_PORT}'
OBJECT_COUNT='${OBJECT_COUNT}'
OBJECT_PREFIX='${OBJECT_PREFIX}'
HARNESS_IMAGE='${HARNESS_IMAGE}'
ECR_REGISTRY="\${ACCOUNT_ID}.dkr.ecr.\${REGION}.amazonaws.com"

aws ecr get-login-password --region "\$REGION" \
  | docker login --username AWS --password-stdin "\$ECR_REGISTRY"

docker pull "\$HARNESS_IMAGE"
docker rm -f s3x-harness 2>/dev/null || true
docker run -d --name s3x-harness --restart unless-stopped \
  -p "\${HARNESS_PORT}:8080" \
  -e AWS_REGION="\$REGION" \
  -e AWS_DEFAULT_REGION="\$REGION" \
  -e EXPRESS_BUCKET="\$EXPRESS_BUCKET" \
  -e STANDARD_BUCKET="\$STANDARD_BUCKET" \
  -e OBJECT_COUNT="\$OBJECT_COUNT" \
  -e OBJECT_PREFIX="\$OBJECT_PREFIX" \
  "\$HARNESS_IMAGE"

echo bootstrap-complete
EOF
}

cmd_up() {
  require_env
  need_jq
  command -v dd >/dev/null 2>&1 || command -v head >/dev/null 2>&1 || die "dd or head required to seed objects"
  ensure_suffix
  mkdir -p "$WORK_DIR"
  resolve_az_name

  ACCOUNT_ID="$(aws_cli sts get-caller-identity --query Account --output text)"
  resolve_harness_image
  ROLE_NAME="${NAME_PREFIX}-${LAB_SUFFIX}-ec2"
  INSTANCE_PROFILE="${NAME_PREFIX}-${LAB_SUFFIX}-profile"
  STANDARD_BUCKET="${NAME_PREFIX}-${LAB_SUFFIX}-${ACCOUNT_ID}"
  EXPRESS_BUCKET="${NAME_PREFIX}-${LAB_SUFFIX}--${EXPRESS_AZ_ID}--x-s3"
  DASH_CIDR="${DASH_CIDR:-0.0.0.0/0}"

  printf 'Creating dedicated VPC %s in %s (%s)…\n' "$VPC_CIDR" "$AWS_REGION" "$AZ_NAME" >&2

  VPC_ID="$(
    aws_ec2 create-vpc \
      --cidr-block "$VPC_CIDR" \
      --tag-specifications "$(tag_spec vpc)" \
      --query 'Vpc.VpcId' --output text
  )"
  aws_ec2 modify-vpc-attribute --vpc-id "$VPC_ID" --enable-dns-support '{"Value":true}'
  aws_ec2 modify-vpc-attribute --vpc-id "$VPC_ID" --enable-dns-hostnames '{"Value":true}'

  IGW_ID="$(
    aws_ec2 create-internet-gateway \
      --tag-specifications "$(tag_spec internet-gateway)" \
      --query 'InternetGateway.InternetGatewayId' --output text
  )"
  aws_ec2 attach-internet-gateway --internet-gateway-id "$IGW_ID" --vpc-id "$VPC_ID"

  SUBNET_ID="$(
    aws_ec2 create-subnet \
      --vpc-id "$VPC_ID" \
      --cidr-block "$SUBNET_CIDR" \
      --availability-zone "$AZ_NAME" \
      --tag-specifications "$(tag_spec subnet)" \
      --query 'Subnet.SubnetId' --output text
  )"
  aws_ec2 modify-subnet-attribute --subnet-id "$SUBNET_ID" --map-public-ip-on-launch

  RTB_ID="$(
    aws_ec2 create-route-table \
      --vpc-id "$VPC_ID" \
      --tag-specifications "$(tag_spec route-table)" \
      --query 'RouteTable.RouteTableId' --output text
  )"
  aws_ec2 create-route --route-table-id "$RTB_ID" --destination-cidr-block 0.0.0.0/0 --gateway-id "$IGW_ID" >/dev/null
  aws_ec2 associate-route-table --route-table-id "$RTB_ID" --subnet-id "$SUBNET_ID" >/dev/null

  SG_ID="$(
    aws_ec2 create-security-group \
      --group-name "${NAME_PREFIX}-${LAB_SUFFIX}-sg" \
      --description "S3 Express hot lookup harness" \
      --vpc-id "$VPC_ID" \
      --tag-specifications "$(tag_spec security-group)" \
      --query 'GroupId' --output text
  )"
  aws_ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --ip-permissions "IpProtocol=tcp,FromPort=${HARNESS_PORT},ToPort=${HARNESS_PORT},IpRanges=[{CidrIp=${DASH_CIDR},Description=harness-dash}]" \
    >/dev/null
  # Egress is open by default on new SGs.

  # General-purpose S3 (harness artifact + Standard bakeoff) and S3 Express
  # (directory bucket data plane) each need their own gateway endpoint.
  # https://docs.aws.amazon.com/AmazonS3/latest/userguide/directory-bucket-az-networking.html
  VPCE_S3_ID="$(
    aws_ec2 create-vpc-endpoint \
      --vpc-id "$VPC_ID" \
      --vpc-endpoint-type Gateway \
      --service-name "com.amazonaws.${AWS_REGION}.s3" \
      --route-table-ids "$RTB_ID" \
      --tag-specifications "$(tag_spec vpc-endpoint)" \
      --query 'VpcEndpoint.VpcEndpointId' --output text
  )"
  VPCE_S3EXPRESS_ID="$(
    aws_ec2 create-vpc-endpoint \
      --vpc-id "$VPC_ID" \
      --vpc-endpoint-type Gateway \
      --service-name "com.amazonaws.${AWS_REGION}.s3express" \
      --route-table-ids "$RTB_ID" \
      --tag-specifications "$(tag_spec vpc-endpoint)" \
      --query 'VpcEndpoint.VpcEndpointId' --output text
  )"

  # --- IAM ---
  # Object ops on directory buckets are authorized via CreateSession only.
  # https://docs.aws.amazon.com/AmazonS3/latest/userguide/s3-express-authenticating-authorizing.html
  local trust_file perms_file
  trust_file="${WORK_DIR}/ec2-trust.json"
  perms_file="${WORK_DIR}/ec2-perms.json"
  cat >"$trust_file" <<'JSON'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "ec2.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
JSON
  cat >"$perms_file" <<JSON
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "StandardBucket",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::${STANDARD_BUCKET}",
        "arn:aws:s3:::${STANDARD_BUCKET}/*"
      ]
    },
    {
      "Sid": "ExpressCreateSession",
      "Effect": "Allow",
      "Action": "s3express:CreateSession",
      "Resource": "arn:aws:s3express:${AWS_REGION}:${ACCOUNT_ID}:bucket/${EXPRESS_BUCKET}"
    },
    {
      "Sid": "EcrAuth",
      "Effect": "Allow",
      "Action": ["ecr:GetAuthorizationToken"],
      "Resource": "*"
    },
    {
      "Sid": "EcrPull",
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage"
      ],
      "Resource": "arn:aws:ecr:${AWS_REGION}:${ACCOUNT_ID}:repository/${ECR_REPO_NAME}"
    }
  ]
}
JSON

  aws_cli iam create-role \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document "file://${trust_file}" \
    --tags "Key=${TAG_KEY},Value=${TAG_VALUE}" >/dev/null
  aws_cli iam put-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-name "${NAME_PREFIX}-s3" \
    --policy-document "file://${perms_file}"
  # Session Manager / Run Command (AL2023 ships SSM Agent).
  # https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-getting-started-instance-profile.html
  aws_cli iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
  aws_cli iam create-instance-profile --instance-profile-name "$INSTANCE_PROFILE" >/dev/null || true
  aws_cli iam add-role-to-instance-profile \
    --instance-profile-name "$INSTANCE_PROFILE" \
    --role-name "$ROLE_NAME" >/dev/null
  # Instance profiles need a short propagation window.
  sleep 8

  # --- Buckets ---
  if [[ "$AWS_REGION" == "us-east-1" ]]; then
    aws_cli s3api create-bucket --bucket "$STANDARD_BUCKET"
  else
    aws_cli s3api create-bucket \
      --bucket "$STANDARD_BUCKET" \
      --create-bucket-configuration "LocationConstraint=${AWS_REGION}"
  fi
  aws_cli s3api put-bucket-tagging \
    --bucket "$STANDARD_BUCKET" \
    --tagging "TagSet=[{Key=${TAG_KEY},Value=${TAG_VALUE}}]"

  aws_cli s3api create-bucket \
    --bucket "$EXPRESS_BUCKET" \
    --create-bucket-configuration "Location={Type=AvailabilityZone,Name=${EXPRESS_AZ_ID}},Bucket={DataRedundancy=SingleAvailabilityZone,Type=Directory}"

  # Directory buckets use S3 Control TagResource (not s3api put-bucket-tagging).
  # https://docs.aws.amazon.com/AmazonS3/latest/userguide/directory-buckets-tagging.html
  aws_cli s3control tag-resource \
    --account-id "$ACCOUNT_ID" \
    --resource-arn "arn:aws:s3express:${AWS_REGION}:${ACCOUNT_ID}:bucket/${EXPRESS_BUCKET}" \
    --tags "Key=${TAG_KEY},Value=${TAG_VALUE}"

  seed_objects

  # --- EC2 ---
  local ami_id userdata_file
  ami_id="$(
    aws_cli ssm get-parameters \
      --names /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64 \
      --query 'Parameters[0].Value' --output text
  )"
  userdata_file="${WORK_DIR}/user-data.sh"
  build_user_data >"$userdata_file"

  INSTANCE_ID="$(
    aws_ec2 run-instances \
      --image-id "$ami_id" \
      --instance-type "$INSTANCE_TYPE" \
      --subnet-id "$SUBNET_ID" \
      --security-group-ids "$SG_ID" \
      --iam-instance-profile "Name=${INSTANCE_PROFILE}" \
      --user-data "file://${userdata_file}" \
      --metadata-options "HttpTokens=required,HttpPutResponseHopLimit=2,HttpEndpoint=enabled" \
      --tag-specifications "$(tag_spec instance)" \
      --query 'Instances[0].InstanceId' --output text
  )"

  printf 'Waiting for instance %s…\n' "$INSTANCE_ID" >&2
  aws_ec2 wait instance-running --instance-ids "$INSTANCE_ID"
  PUBLIC_IP="$(
    aws_ec2 describe-instances \
      --instance-ids "$INSTANCE_ID" \
      --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
  )"

  write_state

  cat <<EOF

Lab is up (bootstrap continues for a few minutes on the instance).

  VPC              $VPC_ID
  Subnet           $SUBNET_ID ($AZ_NAME / $EXPRESS_AZ_ID)
  S3 gateway EP    $VPCE_S3_ID
  Express EP       $VPCE_S3EXPRESS_ID
  Standard bucket  s3://$STANDARD_BUCKET
  Express bucket   s3://$EXPRESS_BUCKET
  Harness image    $HARNESS_IMAGE
  Instance         $INSTANCE_ID ($INSTANCE_TYPE)
  Dashboard        http://${PUBLIC_IP}:${HARNESS_PORT}/

Next:
  ./scripts/demo.sh status
  ./scripts/demo.sh dash
EOF
}

refresh_public_ip() {
  [[ -n "${INSTANCE_ID:-}" ]] || return 0
  PUBLIC_IP="$(
    aws_ec2 describe-instances \
      --instance-ids "$INSTANCE_ID" \
      --query 'Reservations[0].Instances[0].PublicIpAddress' --output text 2>/dev/null || true
  )"
  if [[ -n "$PUBLIC_IP" && "$PUBLIC_IP" != "None" ]]; then
    need_jq
    local tmp
    tmp="$(mktemp)"
    jq --arg ip "$PUBLIC_IP" '.publicIp = $ip' "$STATE_FILE" >"$tmp"
    mv "$tmp" "$STATE_FILE"
  fi
}

cmd_status() {
  require_env
  load_state
  refresh_public_ip

  printf 'region=%s profile=%s suffix=%s\n' "$AWS_REGION" "$AWS_PROFILE" "$LAB_SUFFIX"
  printf 'vpc=%s subnet=%s (%s / %s)\n' "$VPC_ID" "$SUBNET_ID" "$AZ_NAME" "$EXPRESS_AZ_ID"
  printf 'standard=%s\n' "$STANDARD_BUCKET"
  printf 'express=%s\n' "$EXPRESS_BUCKET"
  printf 'harness-image=%s\n' "${HARNESS_IMAGE:-n/a}"
  printf 'instance=%s ip=%s type=%s\n' "${INSTANCE_ID:-none}" "${PUBLIC_IP:-none}" "$INSTANCE_TYPE"

  if [[ -n "${INSTANCE_ID:-}" ]]; then
    local state
    state="$(
      aws_ec2 describe-instances \
        --instance-ids "$INSTANCE_ID" \
        --query 'Reservations[0].Instances[0].State.Name' --output text 2>/dev/null || echo unknown
    )"
    printf 'instance-state=%s\n' "$state"
  fi

  local std_count exp_count
  std_count="$(
    aws_cli s3api list-objects-v2 --bucket "$STANDARD_BUCKET" --prefix "$OBJECT_PREFIX" \
      --query 'length(Contents)' --output text 2>/dev/null || echo err
  )"
  exp_count="$(
    aws_cli s3api list-objects-v2 --bucket "$EXPRESS_BUCKET" --prefix "$OBJECT_PREFIX" \
      --query 'length(Contents)' --output text 2>/dev/null || echo err
  )"
  # Empty prefix → JMESPath null/None
  [[ "$std_count" == "None" || "$std_count" == "null" || -z "$std_count" ]] && std_count=0
  [[ "$exp_count" == "None" || "$exp_count" == "null" || -z "$exp_count" ]] && exp_count=0
  printf 'standard-objects=%s express-objects=%s\n' "$std_count" "$exp_count"

  if [[ -n "${PUBLIC_IP:-}" && "$PUBLIC_IP" != "None" ]]; then
    local code
    code="$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 3 "http://${PUBLIC_IP}:${HARNESS_PORT}/healthz" || true)"
    printf 'harness-healthz=%s (http://%s:%s/)\n' "${code:-down}" "$PUBLIC_IP" "$HARNESS_PORT"
  fi
}

cmd_seed() {
  require_env
  load_state
  seed_objects
  printf 'Seeded %s keys under %s on both buckets.\n' "$OBJECT_COUNT" "$OBJECT_PREFIX"
}

cmd_harness() {
  require_env
  load_state
  cat <<EOF
Harness images are built by CodeBuild into ECR (not on the lab EC2).

  Rebuild and push:
    export S3X_LAB_ALLOW_AWS=1
    ./scripts/image.sh build

  Then either:
    - Re-run ./scripts/demo.sh up with a new LAB_SUFFIX (pulls tag from .image-state.json), or
    - On the instance: docker pull ${HARNESS_IMAGE:-<ecr-uri:tag>} && docker restart s3x-harness

Current lab image: ${HARNESS_IMAGE:-unknown}
Dashboard: http://${PUBLIC_IP:-<pending>}:${HARNESS_PORT}/
EOF
}

cmd_dash() {
  require_env
  load_state
  refresh_public_ip
  [[ -n "${PUBLIC_IP:-}" && "$PUBLIC_IP" != "None" ]] || die "No public IP yet. Check: ./scripts/demo.sh status"
  local url="http://${PUBLIC_IP}:${HARNESS_PORT}/"
  printf '%s\n' "$url"
  printf 'Local view (SSM): ./scripts/demo.sh port-forward  →  http://127.0.0.1:%s/\n' \
    "${LOCAL_PORT:-$HARNESS_PORT}" >&2
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$url" >/dev/null 2>&1 || true
  fi
}

cmd_port_forward() {
  require_env
  load_state
  [[ -n "${INSTANCE_ID:-}" && "$INSTANCE_ID" != "null" ]] || die "No instanceId in lab state"
  command -v session-manager-plugin >/dev/null 2>&1 || die \
    "session-manager-plugin not found. Install: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html"
  local local_port="${LOCAL_PORT:-$HARNESS_PORT}"
  local status
  status="$(
    aws_cli ssm get-connection-status --target "$INSTANCE_ID" --query Status --output text 2>/dev/null || echo unknown
  )"
  [[ "$status" == "connected" ]] || die \
    "SSM Status=${status} for ${INSTANCE_ID}. Need AmazonSSMManagedInstanceCore on the instance role (see IAM and EC2)."

  printf 'Forwarding remote :%s → http://127.0.0.1:%s/  (Ctrl+C to stop)\n' \
    "$HARNESS_PORT" "$local_port" >&2
  # https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-sessions-start.html
  aws_cli ssm start-session \
    --target "$INSTANCE_ID" \
    --document-name AWS-StartPortForwardingSession \
    --parameters "{\"portNumber\":[\"${HARNESS_PORT}\"],\"localPortNumber\":[\"${local_port}\"]}"
}

empty_prefix() {
  local bucket="$1"
  local prefix="$2"
  # Delete objects under prefix; directory buckets also support delete-objects.
  local keys
  keys="$(
    aws_cli s3api list-objects-v2 --bucket "$bucket" --prefix "$prefix" \
      --query 'Contents[].Key' --output text 2>/dev/null || true
  )"
  if [[ -z "$keys" || "$keys" == "None" ]]; then
    return 0
  fi
  local key
  for key in $keys; do
    aws_cli s3api delete-object --bucket "$bucket" --key "$key" >/dev/null
  done
}

empty_bucket_all() {
  local bucket="$1"
  # Best-effort: sync delete for general purpose; key loop also covers Express.
  aws_cli s3 rm "s3://${bucket}" --recursive --only-show-errors 2>/dev/null || true
  local token="" cont="true"
  while [[ "$cont" == "true" ]]; do
    local out
    if [[ -n "$token" ]]; then
      out="$(aws_cli s3api list-objects-v2 --bucket "$bucket" --continuation-token "$token" --output json)"
    else
      out="$(aws_cli s3api list-objects-v2 --bucket "$bucket" --output json 2>/dev/null || echo '{}')"
    fi
    local count
    count="$(jq -r '.KeyCount // 0' <<<"$out")"
    if [[ "$count" -gt 0 ]]; then
      jq -c '{Objects: [.Contents[] | {Key: .Key}], Quiet: true}' <<<"$out" >"${WORK_DIR}/delete-batch.json"
      aws_cli s3api delete-objects --bucket "$bucket" --delete "file://${WORK_DIR}/delete-batch.json" >/dev/null || true
    fi
    cont="$(jq -r '.IsTruncated // false' <<<"$out")"
    token="$(jq -r '.NextContinuationToken // empty' <<<"$out")"
    [[ "$cont" == "true" ]] || break
  done
}

cmd_down() {
  require_env
  load_state
  mkdir -p "$WORK_DIR"

  printf 'This will delete VPC %s, buckets, instance, and IAM for LAB_SUFFIX=%s\n' "$VPC_ID" "$LAB_SUFFIX"
  printf 'Type the LAB_SUFFIX to confirm: '
  local confirm
  read -r confirm
  [[ "$confirm" == "$LAB_SUFFIX" ]] || die "Confirmation did not match LAB_SUFFIX"

  if [[ -n "${INSTANCE_ID:-}" && "$INSTANCE_ID" != "null" ]]; then
    aws_ec2 terminate-instances --instance-ids "$INSTANCE_ID" >/dev/null || true
    printf 'Waiting for instance termination…\n' >&2
    aws_ec2 wait instance-terminated --instance-ids "$INSTANCE_ID" || true
  fi

  if [[ -n "${STANDARD_BUCKET:-}" ]]; then
    empty_bucket_all "$STANDARD_BUCKET"
    aws_cli s3api delete-bucket --bucket "$STANDARD_BUCKET" || true
  fi
  if [[ -n "${EXPRESS_BUCKET:-}" ]]; then
    empty_bucket_all "$EXPRESS_BUCKET"
    aws_cli s3api delete-bucket --bucket "$EXPRESS_BUCKET" || true
  fi

  local ep_ids=()
  [[ -n "${VPCE_S3_ID:-}" && "$VPCE_S3_ID" != "null" ]] && ep_ids+=("$VPCE_S3_ID")
  [[ -n "${VPCE_S3EXPRESS_ID:-}" && "$VPCE_S3EXPRESS_ID" != "null" ]] && ep_ids+=("$VPCE_S3EXPRESS_ID")
  if ((${#ep_ids[@]} > 0)); then
    aws_ec2 delete-vpc-endpoints --vpc-endpoint-ids "${ep_ids[@]}" >/dev/null || true
  fi

  if [[ -n "${SG_ID:-}" ]]; then
    # SG may still be attached briefly after terminate.
    local i
    for i in 1 2 3 4 5 6; do
      aws_ec2 delete-security-group --group-id "$SG_ID" >/dev/null 2>&1 && break
      sleep 5
    done
  fi

  if [[ -n "${SUBNET_ID:-}" ]]; then
    aws_ec2 delete-subnet --subnet-id "$SUBNET_ID" || true
  fi
  if [[ -n "${RTB_ID:-}" ]]; then
    # Main RT association may remain; delete custom RT after disassociate is automatic on subnet delete.
    aws_ec2 delete-route-table --route-table-id "$RTB_ID" || true
  fi
  if [[ -n "${IGW_ID:-}" && -n "${VPC_ID:-}" ]]; then
    aws_ec2 detach-internet-gateway --internet-gateway-id "$IGW_ID" --vpc-id "$VPC_ID" || true
    aws_ec2 delete-internet-gateway --internet-gateway-id "$IGW_ID" || true
  fi
  if [[ -n "${VPC_ID:-}" ]]; then
    aws_ec2 delete-vpc --vpc-id "$VPC_ID" || true
  fi

  if [[ -n "${INSTANCE_PROFILE:-}" && -n "${ROLE_NAME:-}" ]]; then
    aws_cli iam remove-role-from-instance-profile \
      --instance-profile-name "$INSTANCE_PROFILE" \
      --role-name "$ROLE_NAME" 2>/dev/null || true
    aws_cli iam delete-instance-profile --instance-profile-name "$INSTANCE_PROFILE" 2>/dev/null || true
    aws_cli iam delete-role-policy --role-name "$ROLE_NAME" --policy-name "${NAME_PREFIX}-s3" 2>/dev/null || true
    aws_cli iam detach-role-policy \
      --role-name "$ROLE_NAME" \
      --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore 2>/dev/null || true
    aws_cli iam delete-role --role-name "$ROLE_NAME" 2>/dev/null || true
  fi

  rm -f "$STATE_FILE"
  printf 'Teardown complete. Removed %s\n' "$STATE_FILE"
}

main() {
  local cmd="${1:-}"
  case "$cmd" in
    up) shift; cmd_up "$@" ;;
    status) shift; cmd_status "$@" ;;
    seed) shift; cmd_seed "$@" ;;
    harness) shift; cmd_harness "$@" ;;
    dash) shift; cmd_dash "$@" ;;
    port-forward) shift; cmd_port_forward "$@" ;;
    down) shift; cmd_down "$@" ;;
    -h|--help|help|"") usage ;;
    *) die "unknown command: $cmd (see --help)" ;;
  esac
}

main "$@"
