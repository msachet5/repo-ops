"""Build UTM-tagged links for a launch, one per channel, so traffic can be attributed.

    python utm_links.py https://github.com/msachet5/forecast-value-added --campaign fva-v0.1 \
        --channels hackernews reddit-datascience linkedin pycoders ibf

Prints a markdown table to paste into the launch checklist. Note: GitHub's own referrer report
ignores UTM parameters, but they show up in the "popular content" paths and in your site analytics
when the link points at a docs site or cleverchainai.com.
"""

from __future__ import annotations

import argparse
from urllib.parse import urlencode, urlparse, urlunparse

MEDIUM = {
    "hackernews": "community", "reddit": "community", "linkedin": "social", "x": "social", "bluesky": "social",
    "pycoders": "newsletter", "newsletter": "newsletter", "ibf": "article", "email": "email", "kaggle": "referral",
}


def tag(url: str, source: str, campaign: str, content: str | None = None) -> str:
    parts = urlparse(url)
    medium = next((m for k, m in MEDIUM.items() if source.startswith(k)), "referral")
    q = {"utm_source": source, "utm_medium": medium, "utm_campaign": campaign}
    if content:
        q["utm_content"] = content
    query = (parts.query + "&" if parts.query else "") + urlencode(q)
    return urlunparse(parts._replace(query=query))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--channels", nargs="+", required=True)
    a = ap.parse_args()
    print("| Channel | Link |\n|---|---|")
    for c in a.channels:
        print(f"| {c} | {tag(a.url, c, a.campaign)} |")


if __name__ == "__main__":
    main()
