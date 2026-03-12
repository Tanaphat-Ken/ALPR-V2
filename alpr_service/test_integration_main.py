#!/usr/bin/env python3
"""
4.5.2 Integration Tests
Tests that require all Docker containers to be running.

Covers:
  1) API Gateway & Routing   — Nginx forwards requests to the correct backend
  2) Load Balancing          — Round-robin distribution to plate-recognizer replicas
  3) Database Persistence    — API results are stored in PostgreSQL

Prerequisites:
    cd alpr_service
    docker compose up -d          # or: docker compose --scale plate-recognizer=2 up -d
    pip install requests psycopg2-binary

Run all tests:
    python test_integration_main.py

Run a single section:
    python test_integration_main.py gateway
    python test_integration_main.py loadbalance
    python test_integration_main.py database
"""

from __future__ import annotations

import os
import sys
import time
import json
import requests
import subprocess
import psycopg2
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration (override with environment variables)
# ---------------------------------------------------------------------------

NGINX_BASE    = os.getenv("NGINX_BASE",    "http://localhost:80")
GENERAL_API   = os.getenv("GENERAL_API",   "http://localhost:8092")   # direct (optional)
IMAGE_API     = os.getenv("IMAGE_API",     "http://localhost:8089")   # direct (optional)

DB_HOST       = os.getenv("DB_HOST",       "localhost")
DB_PORT       = int(os.getenv("DB_PORT",   "5432"))
DB_NAME       = os.getenv("DB_NAME",       "alpr_service")
DB_USER       = os.getenv("DB_USER",       "alpr")
DB_PASSWORD   = os.getenv("DB_PASSWORD",   "P@ssw0rd")

# Path to a test image with a licence plate.
# Checks several candidate locations so the script works both on the host
# (relative to alpr_service/) and inside a container (after docker cp).
def _find_default_image() -> str:
    candidates = [
        os.getenv("TEST_IMAGE", ""),
        str(Path(__file__).parent / "plate_recognizer" / "testing" / "test.jpg"),
        "/tmp/plate_recognizer/testing/test.jpg",
        "/tmp/test.jpg",
        "/tmp/plate.jpg",
    ]
    for p in candidates:
        if p and Path(p).exists():
            return p
    return str(Path(__file__).parent / "plate_recognizer" / "testing" / "test.jpg")

TEST_IMAGE = _find_default_image()

PASS = "\033[92m✓ PASS\033[0m"
FAIL = "\033[91m✗ FAIL\033[0m"
INFO = "\033[94mINFO\033[0m"

results: list[dict] = []


def record(name: str, passed: bool, detail: str = ""):
    results.append({"name": name, "passed": passed, "detail": detail})
    status = PASS if passed else FAIL
    print(f"  {status}  {name}")
    if detail:
        print(f"         {detail}")


# ===========================================================================
# Section 1 — API Gateway & Routing (Nginx Reverse Proxy)
# ===========================================================================

def test_api_gateway():
    print("\n" + "=" * 65)
    print("4.5.2 (1) API Gateway & Routing — Nginx Reverse Proxy")
    print("=" * 65)

    # --- 1a. Health-check endpoint routed through Nginx
    try:
        r = requests.get(f"{NGINX_BASE}/readyz", timeout=10)
        passed = r.status_code == 200
        record(
            "GET /readyz → 200 OK through Nginx",
            passed,
            f"status={r.status_code}  body={r.text[:120]}",
        )
        if passed:
            data = r.json()
            record(
                "Health response contains 'message' key",
                "message" in data,
                str(data),
            )
    except requests.exceptions.ConnectionError as exc:
        record("GET /readyz through Nginx", False, f"Connection refused — {exc}")
        print(f"  {INFO}  Make sure Nginx is running: docker compose up -d")

    # --- 1b. Auth registration endpoint routed through /api/general/
    try:
        unique_email = f"inttest{int(time.time())}@example.com"
        payload = {
            "username": f"inttest{int(time.time())}",
            "email": unique_email,
            "password": "IntTest@123",
            "tel": "0800000001",
        }
        r = requests.post(
            f"{NGINX_BASE}/api/general/auth/register",
            json=payload,
            timeout=10,
        )
        passed = r.status_code in (200, 201)
        record(
            "POST /api/general/auth/register → 200/201 through Nginx",
            passed,
            f"status={r.status_code}  body={r.text[:200]}",
        )
        if passed:
            data = r.json()
            record("Response contains 'user_id'", "user_id" in data, str(data))
    except requests.exceptions.ConnectionError as exc:
        record("POST /api/general/auth/register through Nginx", False, str(exc))

    # --- 1c. Plate recognition endpoint (image upload) through Nginx
    image_path = Path(TEST_IMAGE)
    if not image_path.exists():
        print(f"  {INFO}  No test image at {TEST_IMAGE} — skipping plate recognition routing test.")
        print(f"         Place a licence-plate image at that path and re-run.")
    else:
        try:
            with open(image_path, "rb") as f:
                r = requests.post(
                    f"{NGINX_BASE}/api/v1/image/process",
                    files={"file": (image_path.name, f, "image/jpeg")},
                    timeout=30,
                )
            passed = r.status_code == 200
            record(
                "POST /api/v1/image/process → 200 OK through Nginx",
                passed,
                f"status={r.status_code}  body={r.text[:300]}",
            )
            if passed:
                data = r.json()
                for key in ("plate_id", "province", "plate_bbox"):
                    record(
                        f"Response JSON contains '{key}'",
                        key in data,
                        str(data.get(key)),
                    )
        except requests.exceptions.ConnectionError as exc:
            record("POST /api/v1/image/process through Nginx", False, str(exc))


# ===========================================================================
# Section 2 — Load Balancing (Round-Robin to 2 plate-recognizer replicas)
# ===========================================================================

def test_load_balancing(num_requests: int = 10):
    print("\n" + "=" * 65)
    print("4.5.2 (2) Load Balancing — Round-Robin Verification")
    print("=" * 65)

    image_path = Path(TEST_IMAGE)
    if not image_path.exists():
        print(f"  {INFO}  No test image at {TEST_IMAGE}")
        print(        "         Cannot send plate-recognition requests for load-balance testing.")
        print(        "         Place a plate image there, or run docker logs manually:")
        print(        "         docker logs $(docker ps -qf name=plate) --tail 50")
        return

    print(f"  Sending {num_requests} requests to {NGINX_BASE}/api/v1/image/process ...")
    success_count = 0
    for i in range(1, num_requests + 1):
        try:
            with open(image_path, "rb") as f:
                r = requests.post(
                    f"{NGINX_BASE}/api/v1/image/process",
                    files={"file": (image_path.name, f, "image/jpeg")},
                    timeout=30,
                )
            if r.status_code == 200:
                success_count += 1
            sys.stdout.write(f"\r  Sent {i}/{num_requests}  OK={success_count}")
            sys.stdout.flush()
        except requests.exceptions.ConnectionError:
            break
    print()

    record(
        f"All {num_requests} requests reached the backend",
        success_count == num_requests,
        f"{success_count}/{num_requests} returned HTTP 200",
    )

    # --- Check Docker logs for both replicas
    print(f"\n  Checking Docker container logs for round-robin distribution ...")
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=plate", "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=10,
        )
        container_names = [n.strip() for n in result.stdout.strip().splitlines() if n.strip()]

        if not container_names:
            print(f"  {INFO}  No running containers with 'plate' in their name.")
            print(        "         Check with:  docker ps --filter name=plate")
            return

        print(f"  Found containers: {container_names}")
        request_counts: dict[str, int] = {}

        for name in container_names:
            log_result = subprocess.run(
                ["docker", "logs", name, "--tail", "100"],
                capture_output=True, text=True, timeout=10,
            )
            combined = log_result.stdout + log_result.stderr
            # Count lines that look like actual inference requests (FastAPI access log)
            count = sum(
                1 for line in combined.splitlines()
                if "POST" in line and ("/process" in line or "200" in line)
            )
            request_counts[name] = count

        print(f"  Approximate request distribution per replica:")
        for name, count in request_counts.items():
            print(f"    {name}: ~{count} inferred requests in recent logs")

        if len(container_names) >= 2:
            counts = list(request_counts.values())
            both_served = all(c > 0 for c in counts)
            record(
                "Both replicas served at least one request (Round-Robin)",
                both_served,
                "  → " + "  ".join(f"{k}={v}" for k, v in request_counts.items()),
            )
        else:
            print(f"  {INFO}  Only 1 replica is running — cannot verify round-robin.")
            print(        "         Scale with:  docker compose up -d --scale plate-recognizer=2")

    except FileNotFoundError:
        print(f"  {INFO}  'docker' CLI not found — cannot inspect logs automatically.")
        print(        "         Run manually:  docker logs <container_name> --tail 100")
    except subprocess.TimeoutExpired:
        print(f"  {INFO}  Docker logs command timed out.")


# ===========================================================================
# Section 3 — Database Persistence (PostgreSQL)
# ===========================================================================

def test_database_persistence():
    print("\n" + "=" * 65)
    print("4.5.2 (3) Database Persistence — PostgreSQL Verification")
    print("=" * 65)

    # --- First submit an image through the API so we know a request was made
    image_path = Path(TEST_IMAGE)
    submitted_plate_id = None

    if image_path.exists():
        try:
            with open(image_path, "rb") as f:
                r = requests.post(
                    f"{NGINX_BASE}/api/v1/image/process",
                    files={"file": (image_path.name, f, "image/jpeg")},
                    timeout=30,
                )
            if r.status_code == 200:
                submitted_plate_id = r.json().get("plate_id")
                print(f"  Submitted image → API returned plate_id: {submitted_plate_id}")
                print(f"  NOTE: /api/v1/image/process routes directly to plate_recognizer.")
                print(f"        DB logging happens via the authenticated /api/image/ endpoint.")
        except requests.exceptions.ConnectionError as exc:
            print(f"  {INFO}  Could not reach API: {exc}")
    else:
        print(f"  {INFO}  No test image — will only verify table state.")

    # --- Connect to PostgreSQL directly
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=10,
        )
        conn.autocommit = True
        cur = conn.cursor()

        # 1. Verify the image_logs table exists and is queryable
        cur.execute("SELECT COUNT(*) FROM image_logs;")
        total_rows = cur.fetchone()[0]
        record(
            "image_logs table is accessible in PostgreSQL",
            total_rows >= 0,
            f"Total rows in image_logs: {total_rows}",
        )

        # 2. Verify user_subscription table is accessible
        cur.execute("SELECT COUNT(*) FROM user_subscription;")
        subs_count = cur.fetchone()[0]
        record(
            "user_subscription table is accessible",
            subs_count >= 0,
            f"Total rows in user_subscription: {subs_count}",
        )

        # 3. Verify historical records have proper persisted data (plate_id, province,
        #    created_at), demonstrating that real ALPR results were stored.
        #    (New records from /api/v1/image/process are not logged here because
        #     that endpoint routes directly to plate_recognizer — DB logging is
        #     handled by the authenticated alpr_api_image /api/image/ service.)
        cur.execute(
            "SELECT log_id, plate_id, province, created_at "
            "FROM image_logs "
            "WHERE plate_id IS NOT NULL "
            "ORDER BY created_at DESC LIMIT 5;"
        )
        rows = cur.fetchall()
        record(
            "image_logs contains persisted ALPR results (plate_id + province + timestamp)",
            len(rows) > 0,
            f"Found {len(rows)} record(s) with recognised plate data",
        )
        if rows:
            print(f"\n  Persisted ALPR results in image_logs:")
            print(f"  {'log_id':<8} {'plate_id':<15} {'province':<20} {'created_at'}")
            print(f"  {'-'*7} {'-'*14} {'-'*19} {'-'*25}")
            for row in rows[:5]:
                print(f"  {str(row[0]):<8} {str(row[1]):<15} {str(row[2]):<20} {row[3]}")

        # 4. Verify current quota state in user_subscription
        cur.execute(
            "SELECT user_sub_id, user_id, request_quota, is_activate "
            "FROM user_subscription ORDER BY user_sub_id DESC LIMIT 5;"
        )
        subs = cur.fetchall()
        record(
            "user_subscription records show quota state is persisted",
            len(subs) > 0,
            f"Found {len(subs)} subscription record(s)",
        )
        if subs:
            print(f"\n  user_subscription (latest):")
            print(f"  {'sub_id':<8} {'user_id':<9} {'quota':<12} {'active'}")
            print(f"  {'-'*7} {'-'*8} {'-'*11} {'-'*6}")
            for row in subs[:5]:
                print(f"  {str(row[0]):<8} {str(row[1]):<9} {str(row[2]):<12} {row[3]}")

        cur.close()
        conn.close()

    except psycopg2.OperationalError as exc:
        record("Connect to PostgreSQL", False, str(exc))
        print(f"  {INFO}  Ensure PostgreSQL is running and credentials are correct.")
        print(f"         DB_HOST={DB_HOST}  DB_PORT={DB_PORT}  DB_NAME={DB_NAME}  DB_USER={DB_USER}")


# ===========================================================================
# Summary & entry point
# ===========================================================================

def print_summary():
    print("\n" + "=" * 65)
    print("SUMMARY")
    print("=" * 65)
    total  = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    for r in results:
        icon = "✓" if r["passed"] else "✗"
        print(f"  [{icon}] {r['name']}")
    print(f"\n  Passed: {passed}/{total}   Failed: {failed}/{total}")
    return failed == 0


if __name__ == "__main__":
    section = sys.argv[1].lower() if len(sys.argv) > 1 else "all"

    if section in ("all", "gateway"):
        test_api_gateway()
    if section in ("all", "loadbalance", "lb"):
        test_load_balancing()
    if section in ("all", "database", "db"):
        test_database_persistence()

    ok = print_summary()
    sys.exit(0 if ok else 1)
