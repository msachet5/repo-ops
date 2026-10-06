# repo-ops

Measurement for the open-source portfolio. Keep this repository **private**; it holds traffic data.

| Script | Does |
|---|---|
| `scripts/archive_github_metrics.py` | Archives views, clones, referrers, popular paths, stargazers and a star/fork snapshot for each repo you own. GitHub keeps traffic for 14 days only. |
| `scripts/package_downloads.py` | Logs PyPI downloads from pypistats.org |
| `scripts/utm_links.py` | One UTM-tagged link per launch channel |
| `scripts/weekly_report.py` | Markdown summary of the week (paste into the vault, or point `--out` at a vault note) |
| `.github/workflows/archive.yml` | Runs all of it every Monday and commits `metrics/` |

Setup: create a fine-grained token with **Administration: read** and **Metadata: read** on the public repos, save it as the `METRICS_TOKEN` secret, run the workflow once by hand.

The read-only research token kept in the vault has no scopes and cannot read traffic; do not reuse it here.
