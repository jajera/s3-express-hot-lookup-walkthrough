#!/usr/bin/env python3
"""Same-AZ S3 Express vs Standard GET bakeoff with a built-in dashboard."""

from __future__ import annotations

import json
import os
import random
import statistics
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Deque, Dict, List, Optional
from urllib.parse import urlparse

import boto3
from botocore.config import Config

REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
EXPRESS_BUCKET = os.environ["EXPRESS_BUCKET"]
STANDARD_BUCKET = os.environ["STANDARD_BUCKET"]
OBJECT_PREFIX = os.environ.get("OBJECT_PREFIX", "hot/")
OBJECT_COUNT = int(os.environ.get("OBJECT_COUNT", "64"))
LOOP_SLEEP_MS = int(os.environ.get("LOOP_SLEEP_MS", "50"))
WINDOW_SECONDS = int(os.environ.get("WINDOW_SECONDS", "300"))
PORT = int(os.environ.get("HARNESS_PORT", "8080"))
DASH_PATH = Path(__file__).with_name("dash.html")

# Directory buckets use the zonal s3express endpoint; botocore picks it up from
# the bucket name suffix (--az-id--x-s3) when addressing_style is virtual / auto.
S3 = boto3.client(
    "s3",
    region_name=REGION,
    config=Config(
        retries={"max_attempts": 3, "mode": "standard"},
        connect_timeout=5,
        read_timeout=10,
    ),
)

KEYS = [f"{OBJECT_PREFIX}obj-{i:04d}.bin" for i in range(OBJECT_COUNT)]


class LatencyWindow:
    def __init__(self, window_seconds: int) -> None:
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._samples: Deque[tuple[float, float]] = deque()  # (ts, ms)
        self.errors = 0
        self.total = 0

    def add(self, latency_ms: float, ok: bool) -> None:
        now = time.time()
        with self._lock:
            self.total += 1
            if not ok:
                self.errors += 1
                return
            self._samples.append((now, latency_ms))
            self._trim(now)

    def _trim(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self._samples and self._samples[0][0] < cutoff:
            self._samples.popleft()

    def snapshot(self) -> Dict[str, object]:
        now = time.time()
        with self._lock:
            self._trim(now)
            values = [ms for _, ms in self._samples]
            errors = self.errors
            total = self.total
        if not values:
            return {
                "count": 0,
                "errors": errors,
                "total": total,
                "p50_ms": None,
                "p90_ms": None,
                "p99_ms": None,
                "mean_ms": None,
            }
        values_sorted = sorted(values)
        return {
            "count": len(values),
            "errors": errors,
            "total": total,
            "p50_ms": _percentile(values_sorted, 50),
            "p90_ms": _percentile(values_sorted, 90),
            "p99_ms": _percentile(values_sorted, 99),
            "mean_ms": round(statistics.fmean(values), 3),
        }


def _percentile(sorted_values: List[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return round(sorted_values[0], 3)
    k = (len(sorted_values) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return round(sorted_values[f], 3)
    return round(sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f), 3)


EXPRESS = LatencyWindow(WINDOW_SECONDS)
STANDARD = LatencyWindow(WINDOW_SECONDS)
STARTED_AT = time.time()
_stop = threading.Event()


def get_once(bucket: str, key: str) -> tuple[bool, float]:
    t0 = time.perf_counter()
    try:
        S3.get_object(Bucket=bucket, Key=key)["Body"].read()
        ok = True
    except Exception:
        ok = False
    ms = (time.perf_counter() - t0) * 1000.0
    return ok, ms


def worker_loop() -> None:
    while not _stop.is_set():
        key = random.choice(KEYS)
        ok_e, ms_e = get_once(EXPRESS_BUCKET, key)
        EXPRESS.add(ms_e, ok_e)
        ok_s, ms_s = get_once(STANDARD_BUCKET, key)
        STANDARD.add(ms_s, ok_s)
        _stop.wait(LOOP_SLEEP_MS / 1000.0)


def build_stats() -> Dict[str, object]:
    express = EXPRESS.snapshot()
    standard = STANDARD.snapshot()
    ratio: Optional[float] = None
    if (
        isinstance(express.get("p50_ms"), (int, float))
        and isinstance(standard.get("p50_ms"), (int, float))
        and express["p50_ms"] > 0
    ):
        ratio = round(float(standard["p50_ms"]) / float(express["p50_ms"]), 2)
    return {
        "ok": True,
        "region": REGION,
        "express_bucket": EXPRESS_BUCKET,
        "standard_bucket": STANDARD_BUCKET,
        "object_count": OBJECT_COUNT,
        "object_prefix": OBJECT_PREFIX,
        "window_seconds": WINDOW_SECONDS,
        "uptime_seconds": int(time.time() - STARTED_AT),
        "express": express,
        "standard": standard,
        "standard_over_express_p50": ratio,
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            body = DASH_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/api/stats":
            payload = json.dumps(build_stats()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if path == "/healthz":
            payload = b'{"ok":true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        self.send_error(404)


def main() -> None:
    missing = [k for k in ("EXPRESS_BUCKET", "STANDARD_BUCKET") if not os.environ.get(k)]
    if missing:
        raise SystemExit(f"missing env: {', '.join(missing)}")

    worker = threading.Thread(target=worker_loop, name="bakeoff", daemon=True)
    worker.start()

    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(
        f"harness listening on :{PORT} express={EXPRESS_BUCKET} standard={STANDARD_BUCKET}",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        _stop.set()
        server.server_close()


if __name__ == "__main__":
    main()
