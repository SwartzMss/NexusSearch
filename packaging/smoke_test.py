# SPDX-License-Identifier: AGPL-3.0-or-later
"""Smoke-test a relocated NexusSearch executable."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen


BASE_URL = "http://127.0.0.1:8788"


def get(path: str):
    with urlopen(BASE_URL + path, timeout=5) as response:  # noqa: S310 - localhost smoke test
        return response.status, response.headers.get_content_type(), response.read()


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: smoke_test.py PATH_TO_NEXUSSEARCH_EXE")
    process = subprocess.Popen([sys.argv[1]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    deadline = time.monotonic() + 45
    try:
        while time.monotonic() < deadline:
            try:
                status, content_type, body = get("/health")
                if status == 200 and content_type == "application/json" and json.loads(body) == {"status": "ok"}:
                    break
            except (OSError, URLError, json.JSONDecodeError):
                time.sleep(0.5)
        else:
            raise RuntimeError("NexusSearch did not become healthy")

        status, content_type, body = get("/search?q=NVIDIA&format=json")
        if status != 200 or content_type != "application/json":
            raise RuntimeError(f"unexpected search response: {status} {content_type}")
        result = json.loads(body)
        if not isinstance(result, dict) or not isinstance(result.get("results"), list):
            raise RuntimeError("search response has no results list")
        for item in result["results"]:
            if not all(key in item for key in ("title", "url", "content")):
                raise RuntimeError("search result is missing a required field")
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
