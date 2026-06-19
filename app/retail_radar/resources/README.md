# Resources -- real scrape targets

`scrape_targets.json` is the live counterpart to `../config/sources.json` (which scores
credibility). Same source names in both files, so they join cleanly. This file lists where to
actually pull data from, by source:

| Source | Auth needed? | Status |
| --- | --- | --- |
| Google Trends | No (use `pytrends`) | Confirmed reachable; rate-limits, cache results |
| Reddit | No (public RSS) | **Working fetcher included** -- `fetch_reddit.py` |
| Pinterest | No free API | Manual-research only, see note in JSON |
| Bachli Bergsport, Transa | No public API | Premium specialist gap check -- site search, verify path before automating |
| Ochsner Sport, SportXX, Decathlon Switzerland | No public API | Mass-market gap check -- site search, verify path before automating |
| Galaxus / Digitec, Zalando, Amazon | No key, but ToS-restricted scraping | Marketplace demand check -- site search, verify path before automating |
| Brack.ch, Microspot, Manor, Globus | No public API | Generalist mega-mall / department store -- secondary/lifestyle-crossover signal, not a primary gap check |
| BFS (Swiss Federal Statistical Office) | No key | Topic pages + STAT-TAB open data |
| Gear media / newspapers | No key | Per-site search/RSS |

## What's verified vs. what needs a live check

I tested outbound connectivity from this environment: Reddit, Google Trends, and BFS all
responded (not down). Reddit's RSS feed is **confirmed working** -- see `fetch_reddit.py`, which
just pulled live posts from r/trailrunning, including a real mention of "La Sportiva Prodigio
Max" (the same brand used as a worked example in `ARCHITECTURE.md`).

The `url_template` search-path syntax for Galaxus/Zalando/Ochsner/Bachli/Transa (e.g.
`?q={keyword}`) is a best-effort guess at common e-commerce search conventions, **not verified
live** -- open the site, run a real search, and copy the exact resulting URL pattern before
wiring a scraper to it. Don't trust the template blindly.

## Using this for real (not seed) data

```bash
# Reddit -- works right now, no setup
python3 -m retail_radar.resources.fetch_reddit trailrunning "gravel running"
python3 -m retail_radar.resources.fetch_reddit bikepacking
```

This prints live signals shaped like `Signal` rows (see `../schema.py`). To wire it into the
pipeline instead of seed data, edit `../pipeline/collectors.py::collect()` to call
`fetch_reddit.fetch_subreddit_rss(...)` for each subreddit/keyword you care about, merge with
calls to `pytrends` for Google Trends, and leave everything downstream (cleaner, dedup, scorer,
synthesiser) untouched -- they only care about the `Signal` shape, not where it came from.

## Legal/ToS note

Marketplace and competitor sites (Galaxus, Zalando, Amazon, Ochsner, Bachli, Transa) generally
restrict automated scraping in their Terms of Service. For a hackathon demo, prefer:
- manual spot-checks (a person visits the site, logs what they see into `seed_signals.json`), or
- official APIs/affiliate feeds where the company offers one (Amazon Product Advertising API,
  Zalando Partner Program),

over building an unauthenticated scraper against a ToS that disallows it.
