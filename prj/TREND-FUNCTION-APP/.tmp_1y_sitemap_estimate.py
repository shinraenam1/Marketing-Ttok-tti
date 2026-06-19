import json
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from src.collectors.web_meme_collectors import SOURCE_CONFIGS, WebMemeCollector

cutoff = datetime.now(timezone.utc) - timedelta(days=365)
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "ko-KR,ko;q=0.9",
})
collector = WebMemeCollector()

def parse_dt(s: str):
    try:
        return collector._parse_datetime_candidate(s)
    except Exception:
        return None

def crawl_sitemap(start_url: str, max_visits: int = 30):
    queue = [start_url]
    visited = set()
    urls = []
    while queue and len(visited) < max_visits:
        u = queue.pop(0)
        if u in visited:
            continue
        visited.add(u)
        try:
            r = session.get(u, timeout=10)
            r.raise_for_status()
        except Exception:
            continue
        soup = BeautifulSoup(r.text, "html.parser")

        # sitemap index
        for sm in soup.select("sitemap loc"):
            sm_url = sm.get_text(" ", strip=True)
            if sm_url and sm_url not in visited:
                queue.append(sm_url)

        # urlset
        for url_node in soup.select("url"):
            loc_node = url_node.select_one("loc")
            if not loc_node:
                continue
            loc = loc_node.get_text(" ", strip=True)
            lastmod_node = url_node.select_one("lastmod")
            lastmod = parse_dt(lastmod_node.get_text(" ", strip=True)) if lastmod_node else None
            urls.append((loc, lastmod))
    return urls

result = {}
for src in SOURCE_CONFIGS:
    parsed = urlparse(src.url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    seeds = [f"{base}/sitemap.xml", f"{base}/sitemap_index.xml", f"{base}/wp-sitemap.xml"]

    candidates = []
    for seed in seeds:
        candidates.extend(crawl_sitemap(seed, max_visits=20))

    uniq = {}
    for loc, lastmod in candidates:
        if not loc or not loc.startswith("http"):
            continue
        if not collector._is_valid_article_link(src.name, loc, "article"):
            continue
        prev = uniq.get(loc)
        if prev is None or (lastmod and (not prev or lastmod > prev)):
            uniq[loc] = lastmod

    within = 0
    unknown = 0
    for _, dt in uniq.items():
        if dt is None:
            unknown += 1
        elif dt >= cutoff:
            within += 1

    result[src.name] = {
        "estimated_within_1y": within,
        "date_unknown": unknown,
        "unique_article_urls_seen": len(uniq),
    }

out = {
    "as_of": datetime.now(timezone.utc).isoformat(),
    "method": "sitemap_estimate",
    "sources": result,
}
with open("c:/Users/User/trend-function-app/.tmp_1y_sitemap_estimate.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
