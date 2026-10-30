"""Smoke test for the live site, run by the smoke-test job after every deploy.

1. Waits until GET /health reports the commit SHA that was just pushed.
2. Then checks three live requests:
   a. GET  /            -> the page loads and shows the frontend
   b. POST /api/run     -> divide(10, 4) returns 2.5
   c. POST /api/run     -> divide(1, 0) reports ZeroDivisionError

Usage: python scripts/smoke_test.py --url https://my-app.onrender.com --sha <commit sha>
Only the standard library is used, so no install step is needed.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request


def request(url, data=None, timeout=30):
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "smoke-test"},
        method="GET" if data is None else "POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return res.status, res.read().decode()


def wait_for_sha(base, sha, timeout, interval):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        try:
            status, text = request(f"{base}/health")
            live = json.loads(text).get("sha")
            if live != last:
                print(f"/health -> HTTP {status}, sha={live}")
                last = live
            if status == 200 and live == sha:
                return True
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            print(f"/health not ready yet: {exc}")
        time.sleep(interval)
    return False


def check(name, condition, detail):
    print(("PASS " if condition else "FAIL ") + name + ("" if condition else f": {detail}"))
    return condition


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="live base URL")
    parser.add_argument("--sha", required=True, help="commit SHA expected on /health")
    parser.add_argument("--timeout", type=int, default=900, help="seconds to wait for the deploy")
    parser.add_argument("--interval", type=int, default=15, help="seconds between /health polls")
    args = parser.parse_args(argv)
    base = args.url.rstrip("/")

    print(f"Waiting for {base} to serve commit {args.sha} ...")
    if not wait_for_sha(base, args.sha, args.timeout, args.interval):
        print(f"FAIL: live site did not report {args.sha} within {args.timeout}s")
        return 1
    print("New commit is live.\n")

    results = []

    status, html = request(f"{base}/")
    results.append(
        check(
            "GET / shows the frontend",
            status == 200 and "target.py" in html and 'data-fn="divide"' in html,
            f"HTTP {status}",
        )
    )

    status, text = request(f"{base}/api/run", {"function": "divide", "args": ["10", "4"]})
    data = json.loads(text)
    results.append(
        check(
            "divide(10, 4) == 2.5",
            status == 200 and data.get("ok") is True and data.get("result") == "2.5",
            data,
        )
    )

    status, text = request(f"{base}/api/run", {"function": "divide", "args": ["1", "0"]})
    data = json.loads(text)
    results.append(
        check(
            "divide(1, 0) raises ZeroDivisionError",
            status == 200 and data.get("error") == "ZeroDivisionError",
            data,
        )
    )

    print(f"\n{sum(results)}/{len(results)} live checks passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
