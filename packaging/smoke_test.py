# SPDX-License-Identifier: AGPL-3.0-or-later
"""Smoke-test a relocated NexusSearch executable."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


BASE_URL = "http://127.0.0.1:8788"


def get(path: str):
    with urlopen(BASE_URL + path, timeout=5) as response:  # noqa: S310 - localhost smoke test
        return response.status, response.headers.get_content_type(), response.read()


def stop_process(process: subprocess.Popen, stdout_file, stderr_file, stdout_path: Path, stderr_path: Path) -> str:
    """Stop a child and return its captured diagnostics."""
    if process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
    stdout_file.close()
    stderr_file.close()
    stdout = stdout_path.read_text(encoding="utf-8", errors="replace")
    stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
    return f"exit code: {process.returncode}\nstdout:\n{stdout}\nstderr:\n{stderr}"


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: smoke_test.py PATH_TO_NEXUSSEARCH_EXE")
    with tempfile.TemporaryDirectory() as temporary_directory:
        stdout_path = Path(temporary_directory) / "stdout.log"
        stderr_path = Path(temporary_directory) / "stderr.log"
        stdout_file = stdout_path.open("w", encoding="utf-8")
        stderr_file = stderr_path.open("w", encoding="utf-8")
        process = subprocess.Popen([sys.argv[1]], stdout=stdout_file, stderr=stderr_file)
        smoke_error = None
        try:
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                exit_code = process.poll()
                if exit_code is not None:
                    raise RuntimeError(f"NexusSearch exited before becoming healthy (exit code {exit_code})")
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
        except Exception as error:
            smoke_error = error

        diagnostics = stop_process(process, stdout_file, stderr_file, stdout_path, stderr_path)
        if smoke_error is not None:
            raise RuntimeError(f"{smoke_error}\n\n{diagnostics}") from smoke_error
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
