import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from archive_github_metrics import append_unique, archive_repo  # noqa: E402
from utm_links import tag  # noqa: E402


class FakeGH:
    def get(self, path, accept=None, params=None):
        if path.endswith("/traffic/views"):
            return {"views": [{"timestamp": "2026-10-01T00:00:00Z", "count": 10, "uniques": 4}]}
        if path.endswith("/traffic/clones"):
            return {"clones": [{"timestamp": "2026-10-01T00:00:00Z", "count": 2, "uniques": 1}]}
        if path.endswith("/referrers"):
            return [{"referrer": "news.ycombinator.com", "count": 50, "uniques": 30}]
        if path.endswith("/paths"):
            return [{"path": "/msachet5/x", "title": "x", "count": 9, "uniques": 5}]
        return {"stargazers_count": 3, "forks_count": 1, "subscribers_count": 2, "open_issues_count": 0}

    def paged(self, path, accept=None):
        return [{"starred_at": "2026-10-01T10:00:00Z", "user": {"login": "alice", "html_url": "https://github.com/alice"}}]


def test_archive_and_dedupe(tmp_path):
    first = archive_repo(FakeGH(), "o/r", tmp_path, "2026-10-02")
    again = archive_repo(FakeGH(), "o/r", tmp_path, "2026-10-02")
    assert first["views"] == 1 and first["stargazers"] == 1
    assert all(v == 0 for v in again.values())
    rows = list(csv.DictReader((tmp_path / "referrers.csv").open()))
    assert rows[0]["referrer"] == "news.ycombinator.com"


def test_append_unique_empty(tmp_path):
    assert append_unique(tmp_path / "x.csv", [], ("a",)) == 0


def test_utm():
    u = tag("https://github.com/a/b?tab=readme", "reddit-datascience", "fva-v0.1")
    assert "tab=readme&utm_source=reddit-datascience&utm_medium=community&utm_campaign=fva-v0.1" in u
