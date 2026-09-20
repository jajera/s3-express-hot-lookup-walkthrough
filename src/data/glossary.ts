export type GlossaryEntry =
  | string
  | {
      definition: string;
      url?: string;
      urlLabel?: string;
    };

/**
 * Glossary keys are lowercase kebab-case, sorted alphabetically.
 * Keep this list in lockstep with .kiro/steering/glossary.md.
 */
export const glossary: Record<string, GlossaryEntry> = {
  "az-id":
    "Availability Zone ID — a unique, account-stable identifier such as apse2-az1. Directory bucket names and Express location config use the AZ ID, not the account-local AZ name (for example ap-southeast-2a).",
  "create-session":
    "s3express:CreateSession — session-based auth for zonal (object-level) operations on a directory bucket. The SDK or CLI obtains temporary credentials scoped to that bucket before GET/PUT/LIST.",
  "directory-bucket":
    "S3 bucket type that hosts the S3 Express One Zone storage class. Names follow bucket-base-name--zone-id--x-s3 and live in a single Availability Zone.",
  "gateway-endpoint":
    "VPC gateway endpoint for private S3 access without a NAT gateway. This lab creates both com.amazonaws.ap-southeast-2.s3 and com.amazonaws.ap-southeast-2.s3express.",
  harness:
    "Docker container on the lab EC2 instance that continuously GETs the same keys from Express and Standard, exposes a dashboard on :8080, and reports p50/p90 latency ratios.",
  "s3-express": {
    definition:
      "Amazon S3 Express One Zone — single-AZ storage class optimized for consistent single-digit millisecond latency, used only with directory buckets.",
    url: "https://aws.amazon.com/s3/storage-classes/express-one-zone/",
    urlLabel: "S3 Express One Zone",
  },
  "shared-hot-lookup":
    "Workload pattern where many clients repeatedly read a small, shared set of keys (config, feature flags, hot catalog rows). Express co-located with compute is a fit when GET latency dominates.",
};

export function resolveGlossaryEntry(entry: GlossaryEntry | undefined) {
  if (!entry) return { definition: undefined, url: undefined, urlLabel: undefined };
  if (typeof entry === "string") {
    return { definition: entry, url: undefined, urlLabel: undefined };
  }
  return {
    definition: entry.definition,
    url: entry.url,
    urlLabel: entry.urlLabel ?? entry.url,
  };
}
