"""Archive GitHub traffic and stargazers for your own repos before GitHub forgets them.

GitHub keeps only 14 days of traffic (views, clones, referrers, popular paths), and since
mid-2026 only owners and collaborators can list a repo's stargazers. As the owner you can
still read both, so archive them weekly.

    GITHUB_TOKEN=... python archive_github_metrics.py msachet5/forecast-value-added msachet5/planner-skills --out metrics/

Token: a fine-grained token with "Administration: read" (traffic) and "Metadata: read" on the repos,
or the workflow's GITHUB_TOKEN for the repo it runs in. Appends to CSVs and de-duplicates, so
running it more often than weekly is harmless.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

API = "https://api.github.com"


class GitHub:
    def __init__(self, token: str | None, session: requests.Session | None = None):
        self.s = session or requests.Session()
        self.s.headers.update({"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
        if token:
            self.s.headers["Authorization"] = f"Bearer {token}"

    def get(self, path: str, accept: str | None = None, params: dict | None = None) -> Any:
        headers = {"Accept": accept} if accept else None
        r = self.s.get(f"{API}{path}", headers=headers, params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def paged(self, path: str, accept: str | None = None) -> list[Any]:
        out, page = [], 1
        while True:
            batch = self.get(path, accept=accept, params={"per_page": 100, "page": page})
            if not batch:
                return out
            out.extend(batch)
            if len(batch) < 100:
                return out
            page += 1


def append_unique(path: Path, rows: list[dict[str, Any]], key: tuple[str, ...]) -> int:
    """Append rows whose key is not already in the CSV. Returns the number added."""
    if not rows:
        return 0
    existing: set[tuple] = set()
    fieldnames = list(rows[0].keys())
    if path.exists():
        with path.open(newline="") as fh:
            reader = csv.DictReader(fh)
            fieldnames = reader.fieldnames or fieldnames
            existing = {tuple(r[k] for k in key) for r in reader}
    new = [r for r in rows if tuple(str(r[k]) for k in key) not in existing]
    if not new:
        return 0
    write_header = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        if write_header:
            w.writeheader()
        w.writerows(new)
    return len(new)


def archive_repo(gh: GitHub, repo: str, out: Path, today: str) -> dict[str, int]:
    added: dict[str, int] = {}
    views = gh.get(f"/repos/{repo}/traffic/views")
    added["views"] = append_unique(out / "views.csv", [
        {"repo": repo, "date": v["timestamp"][:10], "views": v["count"], "uniques": v["uniques"]} for v in views.get("views", [])
    ], ("repo", "date"))
    clones = gh.get(f"/repos/{repo}/traffic/clones")
    added["clones"] = append_unique(out / "clones.csv", [
        {"repo": repo, "date": c["timestamp"][:10], "clones": c["count"], "uniques": c["uniques"]} for c in clones.get("clones", [])
    ], ("repo", "date"))
    refs = gh.get(f"/repos/{repo}/traffic/popular/referrers")
    added["referrers"] = append_unique(out / "referrers.csv", [
        {"repo": repo, "captured": today, "referrer": r["referrer"], "count": r["count"], "uniques": r["uniques"]} for r in refs
    ], ("repo", "captured", "referrer"))
    paths = gh.get(f"/repos/{repo}/traffic/popular/paths")
    added["paths"] = append_unique(out / "paths.csv", [
        {"repo": repo, "captured": today, "path": p["path"], "count": p["count"], "uniques": p["uniques"]} for p in paths
    ], ("repo", "captured", "path"))
    stars = gh.paged(f"/repos/{repo}/stargazers", accept="application/vnd.github.star+json")
    added["stargazers"] = append_unique(out / "stargazers.csv", [
        {"repo": repo, "starred_at": s.get("starred_at", ""), "login": (s.get("user") or {}).get("login", ""),
         "profile": (s.get("user") or {}).get("html_url", "")} for s in stars
    ], ("repo", "login"))
    info = gh.get(f"/repos/{repo}")
    added["snapshot"] = append_unique(out / "repo_snapshots.csv", [{
        "repo": repo, "captured": today, "stars": info["stargazers_count"], "forks": info["forks_count"],
        "watchers": info.get("subscribers_count", ""), "open_issues": info["open_issues_count"],
    }], ("repo", "captured"))
    return added


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repos", nargs="+", help="owner/name")
    ap.add_argument("--out", default="metrics")
    a = ap.parse_args(argv)
    gh = GitHub(os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ok = True
    for repo in a.repos:
        try:
            added = archive_repo(gh, repo, Path(a.out), today)
            print(repo, added)
        except requests.HTTPError as exc:
            ok = False
            print(f"{repo}: {exc} (traffic needs push or admin access to the repo)", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
