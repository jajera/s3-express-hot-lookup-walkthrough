#!/usr/bin/env bash
# Durable harness image pipeline: ECR repository + CodeBuild project.
#
# Lab runs (demo.sh) stay ephemeral. This stack is shared across lab suffixes:
#   ./scripts/image.sh up|build|status|down
#
# Required env: AWS_REGION, AWS_PROFILE (documented: sandbox / ap-southeast-2)
# Mutating commands need S3X_LAB_ALLOW_AWS=1 when the Kiro guard is active.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_FILE="${ROOT}/.image-state.json"
WORK_DIR="${ROOT}/.lab/image"
TAG_KEY="Project"
TAG_VALUE="s3-express-hot-lookup-walkthrough"
ECR_REPO_NAME="s3x-hotlookup-harness"
CB_PROJECT_NAME="s3x-hotlookup-harness"
CB_ROLE_NAME="s3x-hotlookup-codebuild"
SOURCE_BUCKET_PREFIX="s3x-hotlookup-cb"
DEFAULT_REGION="ap-southeast-2"
# amazonlinux aarch64 standard image with Docker (Graviton / arm64 harness)
CB_IMAGE="aws/codebuild/amazonlinux-aarch64-standard:3.0"

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

usage() {
  cat <<'EOF'
Usage: ./scripts/image.sh <command>

Commands:
  up       Create ECR repo, CodeBuild source bucket, IAM role, CodeBuild project
  build    Zip harness/, upload to S3, start CodeBuild, wait for SUCCEEDED
  status   Show ECR repo, latest image tags, last build (read-only)
  down     Delete CodeBuild project, role, source bucket, ECR repo (after confirm)

Required environment:
  AWS_REGION   Lab Region (documented default: ap-southeast-2)
  AWS_PROFILE  Named AWS CLI profile (documented: sandbox)

Optional:
  IMAGE_TAG              Tag pushed alongside :latest (default: git short SHA or timestamp)
  S3X_LAB_ALLOW_AWS=1    Required for mutating subcommands when the Kiro guard is active

After a successful build, lab bring-up pulls:
  ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/s3x-hotlookup-harness:${IMAGE_TAG:-latest}
EOF
}

run() {
  printf '+ %s\n' "$*" >&2
  "$@"
}

aws_cli() {
  run aws --profile "$AWS_PROFILE" --region "$AWS_REGION" "$@"
}

need_jq() {
  command -v jq >/dev/null 2>&1 || die "jq is required"
}

require_env() {
  [[ -n "${AWS_REGION:-}" ]] || die "AWS_REGION is unset. Example: export AWS_REGION=${DEFAULT_REGION}"
  [[ -n "${AWS_PROFILE:-}" ]] || die "AWS_PROFILE is unset. Example: export AWS_PROFILE=sandbox"
  command -v aws >/dev/null 2>&1 || die "aws CLI not found"
}

write_state() {
  need_jq
  local tmp
  tmp="$(mktemp)"
  jq -n \
    --arg region "$AWS_REGION" \
    --arg profile "$AWS_PROFILE" \
    --arg account "$ACCOUNT_ID" \
    --arg ecr "$ECR_REPO_NAME" \
    --arg ecr_uri "$ECR_URI" \
    --arg project "$CB_PROJECT_NAME" \
    --arg role "$CB_ROLE_NAME" \
    --arg role_arn "$CB_ROLE_ARN" \
    --arg bucket "$SOURCE_BUCKET" \
    --arg image_tag "${IMAGE_TAG:-latest}" \
    '{
      region: $region,
      profile: $profile,
      accountId: $account,
      ecrRepository: $ecr,
      ecrUri: $ecr_uri,
      codeBuildProject: $project,
      codeBuildRole: $role,
      codeBuildRoleArn: $role_arn,
      sourceBucket: $bucket,
      imageTag: $image_tag
    }' >"$tmp"
  mv "$tmp" "$STATE_FILE"
  printf 'Wrote %s\n' "$STATE_FILE"
}

load_state() {
  need_jq
  [[ -f "$STATE_FILE" ]] || die "No image state at ${STATE_FILE}. Run: ./scripts/image.sh up"
  AWS_REGION="$(jq -r '.region' "$STATE_FILE")"
  AWS_PROFILE="$(jq -r '.profile' "$STATE_FILE")"
  ACCOUNT_ID="$(jq -r '.accountId' "$STATE_FILE")"
  ECR_REPO_NAME="$(jq -r '.ecrRepository' "$STATE_FILE")"
  ECR_URI="$(jq -r '.ecrUri' "$STATE_FILE")"
  CB_PROJECT_NAME="$(jq -r '.codeBuildProject' "$STATE_FILE")"
  CB_ROLE_NAME="$(jq -r '.codeBuildRole' "$STATE_FILE")"
  CB_ROLE_ARN="$(jq -r '.codeBuildRoleArn' "$STATE_FILE")"
  SOURCE_BUCKET="$(jq -r '.sourceBucket' "$STATE_FILE")"
  IMAGE_TAG="$(jq -r '.imageTag // "latest"' "$STATE_FILE")"
}

resolve_image_tag() {
  if [[ -n "${IMAGE_TAG:-}" ]]; then
    return 0
  fi
  if command -v git >/dev/null 2>&1 && git -C "$ROOT" rev-parse --short HEAD >/dev/null 2>&1; then
    IMAGE_TAG="$(git -C "$ROOT" rev-parse --short HEAD)"
  else
    IMAGE_TAG="$(date +%Y%m%d%H%M%S)"
  fi
}

cmd_up() {
  require_env
  need_jq
  mkdir -p "$WORK_DIR"

  ACCOUNT_ID="$(aws_cli sts get-caller-identity --query Account --output text)"
  SOURCE_BUCKET="${SOURCE_BUCKET_PREFIX}-${ACCOUNT_ID}"
  ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"
  resolve_image_tag

  # --- ECR ---
  if aws_cli ecr describe-repositories --repository-names "$ECR_REPO_NAME" >/dev/null 2>&1; then
    printf 'ECR repository already exists: %s\n' "$ECR_REPO_NAME" >&2
  else
    aws_cli ecr create-repository \
      --repository-name "$ECR_REPO_NAME" \
      --image-scanning-configuration scanOnPush=true \
      --encryption-configuration encryptionType=AES256 \
      --tags "Key=${TAG_KEY},Value=${TAG_VALUE}" >/dev/null
  fi

  # --- Source bucket for CodeBuild ---
  if aws_cli s3api head-bucket --bucket "$SOURCE_BUCKET" >/dev/null 2>&1; then
    printf 'Source bucket already exists: %s\n' "$SOURCE_BUCKET" >&2
  else
    if [[ "$AWS_REGION" == "us-east-1" ]]; then
      aws_cli s3api create-bucket --bucket "$SOURCE_BUCKET"
    else
      aws_cli s3api create-bucket \
        --bucket "$SOURCE_BUCKET" \
        --create-bucket-configuration "LocationConstraint=${AWS_REGION}"
    fi
    aws_cli s3api put-bucket-tagging \
      --bucket "$SOURCE_BUCKET" \
      --tagging "TagSet=[{Key=${TAG_KEY},Value=${TAG_VALUE}}]"
    aws_cli s3api put-public-access-block \
      --bucket "$SOURCE_BUCKET" \
      --public-access-block-configuration \
      BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
  fi

  # --- CodeBuild service role ---
  local trust_file perms_file
  trust_file="${WORK_DIR}/cb-trust.json"
  perms_file="${WORK_DIR}/cb-perms.json"
  cat >"$trust_file" <<'JSON'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "codebuild.amazonaws.com" },
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
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": [
        "arn:aws:logs:${AWS_REGION}:${ACCOUNT_ID}:log-group:/aws/codebuild/${CB_PROJECT_NAME}",
        "arn:aws:logs:${AWS_REGION}:${ACCOUNT_ID}:log-group:/aws/codebuild/${CB_PROJECT_NAME}:*"
      ]
    },
    {
      "Sid": "SourceBucket",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:GetObjectVersion", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::${SOURCE_BUCKET}",
        "arn:aws:s3:::${SOURCE_BUCKET}/*"
      ]
    },
    {
      "Sid": "EcrAuth",
      "Effect": "Allow",
      "Action": ["ecr:GetAuthorizationToken"],
      "Resource": "*"
    },
    {
      "Sid": "EcrPush",
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:CompleteLayerUpload",
        "ecr:InitiateLayerUpload",
        "ecr:PutImage",
        "ecr:UploadLayerPart",
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer"
      ],
      "Resource": "arn:aws:ecr:${AWS_REGION}:${ACCOUNT_ID}:repository/${ECR_REPO_NAME}"
    }
  ]
}
JSON

  if aws_cli iam get-role --role-name "$CB_ROLE_NAME" >/dev/null 2>&1; then
    printf 'IAM role already exists: %s\n' "$CB_ROLE_NAME" >&2
    aws_cli iam put-role-policy \
      --role-name "$CB_ROLE_NAME" \
      --policy-name "${ECR_REPO_NAME}-build" \
      --policy-document "file://${perms_file}"
  else
    aws_cli iam create-role \
      --role-name "$CB_ROLE_NAME" \
      --assume-role-policy-document "file://${trust_file}" \
      --tags "Key=${TAG_KEY},Value=${TAG_VALUE}" >/dev/null
    aws_cli iam put-role-policy \
      --role-name "$CB_ROLE_NAME" \
      --policy-name "${ECR_REPO_NAME}-build" \
      --policy-document "file://${perms_file}"
    sleep 8
  fi
  CB_ROLE_ARN="$(aws_cli iam get-role --role-name "$CB_ROLE_NAME" --query 'Role.Arn' --output text)"

  # --- CodeBuild project ---
  local project_json
  project_json="${WORK_DIR}/cb-project.json"
  cat >"$project_json" <<JSON
{
  "name": "${CB_PROJECT_NAME}",
  "description": "Build s3x-hotlookup harness image and push to ECR",
  "source": {
    "type": "S3",
    "location": "${SOURCE_BUCKET}/source/harness-src.zip",
    "buildspec": "buildspec.yml"
  },
  "artifacts": { "type": "NO_ARTIFACTS" },
  "environment": {
    "type": "ARM_CONTAINER",
    "image": "${CB_IMAGE}",
    "computeType": "BUILD_GENERAL1_SMALL",
    "privilegedMode": true,
    "environmentVariables": [
      { "name": "IMAGE_REPO_NAME", "value": "${ECR_REPO_NAME}", "type": "PLAINTEXT" },
      { "name": "IMAGE_TAG", "value": "latest", "type": "PLAINTEXT" }
    ]
  },
  "serviceRole": "${CB_ROLE_ARN}",
  "timeoutInMinutes": 30,
  "queuedTimeoutInMinutes": 60,
  "tags": [
    { "key": "${TAG_KEY}", "value": "${TAG_VALUE}" }
  ]
}
JSON

  if aws_cli codebuild batch-get-projects --names "$CB_PROJECT_NAME" \
    --query 'projects[0].name' --output text 2>/dev/null | grep -qx "$CB_PROJECT_NAME"; then
    printf 'CodeBuild project already exists: %s (updating)\n' "$CB_PROJECT_NAME" >&2
    # update-project wants the same shape without name nesting quirks — use CLI flags subset
    aws_cli codebuild update-project \
      --name "$CB_PROJECT_NAME" \
      --source "type=S3,location=${SOURCE_BUCKET}/source/harness-src.zip,buildspec=buildspec.yml" \
      --environment "type=ARM_CONTAINER,image=${CB_IMAGE},computeType=BUILD_GENERAL1_SMALL,privilegedMode=true,environmentVariables=[{name=IMAGE_REPO_NAME,value=${ECR_REPO_NAME},type=PLAINTEXT},{name=IMAGE_TAG,value=latest,type=PLAINTEXT}]" \
      --service-role "$CB_ROLE_ARN" >/dev/null
  else
    aws_cli codebuild create-project --cli-input-json "file://${project_json}" >/dev/null
  fi

  write_state

  cat <<EOF

Image pipeline is ready.

  ECR repository   $ECR_REPO_NAME
  ECR URI          $ECR_URI
  CodeBuild        $CB_PROJECT_NAME
  Source bucket    s3://$SOURCE_BUCKET
  Service role     $CB_ROLE_ARN

Next:
  ./scripts/image.sh build
EOF
}

cmd_build() {
  require_env
  load_state
  need_jq
  mkdir -p "$WORK_DIR"
  resolve_image_tag

  local zip_path="${WORK_DIR}/harness-src.zip"
  rm -f "$zip_path"
  # Zip harness contents at archive root so buildspec.yml and Dockerfile sit together.
  if command -v zip >/dev/null 2>&1; then
    (
      cd "${ROOT}/harness"
      run zip -q -r "$zip_path" buildspec.yml Dockerfile requirements.txt app.py dash.html
    )
  else
    python3 - "$zip_path" "${ROOT}/harness" <<'PY'
import sys, zipfile, os
out, root = sys.argv[1], sys.argv[2]
names = ["buildspec.yml", "Dockerfile", "requirements.txt", "app.py", "dash.html"]
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
    for name in names:
        zf.write(os.path.join(root, name), name)
print(f"Wrote {out}", file=sys.stderr)
PY
  fi
  aws_cli s3 cp "$zip_path" "s3://${SOURCE_BUCKET}/source/harness-src.zip" --only-show-errors

  local build_id
  build_id="$(
    aws_cli codebuild start-build \
      --project-name "$CB_PROJECT_NAME" \
      --environment-variables-override "name=IMAGE_TAG,value=${IMAGE_TAG},type=PLAINTEXT" \
      --query 'build.id' --output text
  )"
  printf 'Started build %s (tag=%s)\n' "$build_id" "$IMAGE_TAG" >&2

  local status="IN_PROGRESS"
  while [[ "$status" == "IN_PROGRESS" || "$status" == "QUEUED" ]]; do
    sleep 5
    status="$(
      aws_cli codebuild batch-get-builds --ids "$build_id" \
        --query 'builds[0].buildStatus' --output text
    )"
    printf '  buildStatus=%s\n' "$status" >&2
  done

  [[ "$status" == "SUCCEEDED" ]] || die "CodeBuild finished with status ${status}. Check CloudWatch Logs for /aws/codebuild/${CB_PROJECT_NAME}"

  # Persist tag used for this successful build.
  local tmp
  tmp="$(mktemp)"
  jq --arg tag "$IMAGE_TAG" '.imageTag = $tag' "$STATE_FILE" >"$tmp"
  mv "$tmp" "$STATE_FILE"

  cat <<EOF

Build succeeded.

  Image  ${ECR_URI}:${IMAGE_TAG}
  Also   ${ECR_URI}:latest

Lab bring-up:
  export HARNESS_IMAGE_TAG=${IMAGE_TAG}
  ./scripts/demo.sh up
EOF
}

cmd_status() {
  require_env
  if [[ -f "$STATE_FILE" ]]; then
    load_state
  else
    ACCOUNT_ID="$(aws_cli sts get-caller-identity --query Account --output text)"
    ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"
    SOURCE_BUCKET="${SOURCE_BUCKET_PREFIX}-${ACCOUNT_ID}"
  fi

  printf 'ecr=%s\n' "$ECR_REPO_NAME"
  printf 'uri=%s\n' "${ECR_URI:-n/a}"
  printf 'tag=%s\n' "${IMAGE_TAG:-latest}"

  if aws_cli ecr describe-repositories --repository-names "$ECR_REPO_NAME" >/dev/null 2>&1; then
    aws_cli ecr describe-images --repository-name "$ECR_REPO_NAME" \
      --query 'sort_by(imageDetails,& imagePushedAt)[-5:].[join(`,`, imageTags || [`<untagged>`]), imagePushedAt, imageSizeInBytes]' \
      --output table || printf 'images=(none yet)\n'
  else
    printf 'ecr=missing (run ./scripts/image.sh up)\n'
  fi

  if aws_cli codebuild batch-get-projects --names "$CB_PROJECT_NAME" \
    --query 'projects[0].name' --output text 2>/dev/null | grep -qx "$CB_PROJECT_NAME"; then
    aws_cli codebuild list-builds-for-project --project-name "$CB_PROJECT_NAME" --max-items 3 \
      --query 'ids' --output text 2>/dev/null | tr '\t' '\n' | while read -r id; do
      [[ -n "$id" && "$id" != "None" ]] || continue
      aws_cli codebuild batch-get-builds --ids "$id" \
        --query 'builds[0].[id,buildStatus,endTime]' --output text
    done
  else
    printf 'codebuild=missing\n'
  fi
}

cmd_down() {
  require_env
  load_state

  printf 'This deletes ECR repo %s, CodeBuild %s, bucket %s, and role %s\n' \
    "$ECR_REPO_NAME" "$CB_PROJECT_NAME" "$SOURCE_BUCKET" "$CB_ROLE_NAME"
  printf 'Type the ECR repository name to confirm: '
  local confirm
  read -r confirm
  [[ "$confirm" == "$ECR_REPO_NAME" ]] || die "Confirmation did not match"

  aws_cli codebuild delete-project --name "$CB_PROJECT_NAME" 2>/dev/null || true

  # Empty source bucket then delete.
  aws_cli s3 rm "s3://${SOURCE_BUCKET}" --recursive --only-show-errors 2>/dev/null || true
  aws_cli s3api delete-bucket --bucket "$SOURCE_BUCKET" 2>/dev/null || true

  # Delete all images then repository.
  local digests
  digests="$(
    aws_cli ecr list-images --repository-name "$ECR_REPO_NAME" \
      --query 'imageIds[*].imageDigest' --output text 2>/dev/null || true
  )"
  if [[ -n "$digests" && "$digests" != "None" ]]; then
    # shellcheck disable=SC2086
    local args=()
    for d in $digests; do
      args+=("imageDigest=${d}")
    done
    aws_cli ecr batch-delete-image --repository-name "$ECR_REPO_NAME" --image-ids "${args[@]}" >/dev/null || true
  fi
  aws_cli ecr delete-repository --repository-name "$ECR_REPO_NAME" --force 2>/dev/null || true

  aws_cli iam delete-role-policy --role-name "$CB_ROLE_NAME" --policy-name "${ECR_REPO_NAME}-build" 2>/dev/null || true
  aws_cli iam delete-role --role-name "$CB_ROLE_NAME" 2>/dev/null || true

  rm -f "$STATE_FILE"
  printf 'Image pipeline teardown complete.\n'
}

main() {
  local cmd="${1:-}"
  case "$cmd" in
    up) shift; cmd_up "$@" ;;
    build) shift; cmd_build "$@" ;;
    status) shift; cmd_status "$@" ;;
    down) shift; cmd_down "$@" ;;
    -h|--help|help|"") usage ;;
    *) die "unknown command: $cmd (see --help)" ;;
  esac
}

main "$@"
