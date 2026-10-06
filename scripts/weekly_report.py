"""Summarise the archived metrics into a markdown note (for the Obsidian vault or a README).

    python weekly_report.py --metrics metrics/ --out "Open Source Metrics.md"
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path


def read(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--metrics", default="metrics")
    ap.add_argument("--out", default="metrics/REPORT.md")
    ap.add_argument("--days", type=int, default=7)
    a = ap.parse_args()
    m = Path(a.metrics)
    since = (date.today() - timedelta(days=a.days)).isoformat()

    snaps = read(m / "repo_snapshots.csv")
    latest: dict[str, dict[str, str]] = {}
    first: dict[str, dict[str, str]] = {}
    for r in sorted(snaps, key=lambda r: r["captured"]):
        latest[r["repo"]] = r
        if r["captured"] >= since and r["repo"] not in first:
            first[r["repo"]] = r
    views = defaultdict(int)
    for r in read(m / "views.csv"):
        if r["date"] >= since:
            views[r["repo"]] += int(r["uniques"])
    new_stars = defaultdict(list)
    for r in read(m / "stargazers.csv"):
        if r["starred_at"][:10] >= since:
            new_stars[r["repo"]].append(r["login"])
    refs = defaultdict(lambda: defaultdict(int))
    for r in read(m / "referrers.csv"):
        if r["captured"] >= since:
            refs[r["repo"]][r["referrer"]] = max(refs[r["repo"]][r["referrer"]], int(r["uniques"]))

    lines = [f"# Open source metrics, week to {date.today().isoformat()}", "", "| Repo | Stars | New stars | Unique visitors | Top referrers |", "|---|---:|---:|---:|---|"]
    for repo, r in sorted(latest.items()):
        top = ", ".join(f"{k} ({v})" for k, v in sorted(refs[repo].items(), key=lambda kv: -kv[1])[:3]) or "-"
        lines.append(f"| {repo} | {r['stars']} | {len(new_stars[repo])} | {views[repo]} | {top} |")
    for repo, who in new_stars.items():
        if who:
            lines += ["", f"New stargazers on {repo}: " + ", ".join(f"[{u}](https://github.com/{u})" for u in who)]
    pypi = read(m / "pypi.csv")
    if pypi:
        lines += ["", "| Package | Last week | Last month |", "|---|---:|---:|"]
        last = {}
        for r in pypi:
            last[r["package"]] = r
        lines += [f"| {p} | {r['last_week']} | {r['last_month']} |" for p, r in last.items()]
    Path(a.out).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
