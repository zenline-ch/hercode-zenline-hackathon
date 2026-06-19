"""Real (not seed) data fetcher: Reddit's public RSS feed, no auth required.

This is the one source in scrape_targets.json that's both auth-free and
safe to automate. Run it directly to see live Reddit posts turned into
Signal-shaped dicts:

    python3 -m retail_radar.resources.fetch_reddit trailrunning "gravel running"

Reddit rate-limits aggressively without a registered app (confirmed: 403
with no User-Agent, 429 on repeated calls) -- add delay/backoff if you
call this for multiple subreddits/keywords in a loop.
"""
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

USER_AGENT = "RetailRadarBot/0.1 (hackathon research script)"
ATOM_NS = "{http://www.w3.org/2005/Atom}"


def fetch_subreddit_rss(subreddit: str, keyword: str | None = None, limit: int = 15) -> list[dict]:
    if keyword:
        url = f"https://www.reddit.com/r/{subreddit}/search.rss?q={urllib.parse.quote(keyword)}&sort=new&restrict_sr=on"
    else:
        url = f"https://www.reddit.com/r/{subreddit}/.rss"

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read()

    root = ET.fromstring(raw)
    entries = root.findall(f"{ATOM_NS}entry")[:limit]

    signals = []
    for entry in entries:
        title = entry.findtext(f"{ATOM_NS}title", default="")
        link_el = entry.find(f"{ATOM_NS}link")
        link = link_el.get("href") if link_el is not None else ""
        published = entry.findtext(f"{ATOM_NS}published", default="")
        observed_at = published[:10] if published else datetime.now(timezone.utc).date().isoformat()

        signals.append({
            "opportunity_id": "",  # fill in during clustering -- this is raw, unclustered evidence
            "opportunity_name": "",
            "source": "Reddit",
            "source_type": "social",
            "market": "US",  # Reddit is US-hosted/English-default; treat as a comparison-market proxy
            "keyword": keyword or subreddit,
            "signal_name": title,
            "url": link,
            "signal_score": 0.5,  # placeholder -- score downstream the same way as seed signals
            "confidence": "low",
            "notes": f"r/{subreddit} post, fetched live via RSS",
            "observed_at": observed_at,
            "artifact_type": "json",
            "artifact_uri": url,
            "created_by_tool": "fetch_reddit.py",
        })
    return signals


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 -m retail_radar.resources.fetch_reddit <subreddit> [keyword]")
        sys.exit(1)
    sub = sys.argv[1]
    kw = sys.argv[2] if len(sys.argv) > 2 else None
    for s in fetch_subreddit_rss(sub, kw):
        print(f"- [{s['observed_at']}] {s['signal_name']} -> {s['url']}")
