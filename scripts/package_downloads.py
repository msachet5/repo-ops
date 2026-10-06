"""Log PyPI downloads (pypistats.org) for your packages into a CSV.

    python package_downloads.py forecast-value-added cscpi --out metrics/pypi.csv
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

import requests


def recent(package: str) -> dict:
    r = requests.get(f"https://pypistats.org/api/packages/{package}/recent", timeout=30, headers={"User-Agent": "repo-ops"})
    if r.status_code == 404:
        return {"last_day": 0, "last_week": 0, "last_month": 0, "note": "not on PyPI yet"}
    r.raise_for_status()
    return r.json()["data"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("packages", nargs="+")
    ap.add_argument("--out", default="metrics/pypi.csv")
    a = ap.parse_args()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    new = not out.exists()
    with out.open("a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["captured", "package", "last_day", "last_week", "last_month"])
        for p in a.packages:
            d = recent(p)
            w.writerow([today, p, d.get("last_day"), d.get("last_week"), d.get("last_month")])
            print(p, d)


if __name__ == "__main__":
    main()
