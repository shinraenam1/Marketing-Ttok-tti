from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser


RAW_TOKEN_RE = re.compile(r"[0-9A-Za-z\uac00-\ud7a3]{2,12}")
SCRAPE_STOPWORDS = {
    "있어요",
    "있습니다",
    "있는",
    "있다",
    "가장",
    "요즘",
    "지금",
    "이것",
    "그것",
    "저것",
    "우리",
    "여기",
    "저기",
    "정리",
    "총정리",
    "모음",
    "추천",
    "콘텐츠",
    "소개",
    "보기",
    "방법",
    "사람",
    "사람들",
    "경우",
    "관련",
    "중인",
    "통해",
    "대해",
    "대한",
    "부터",
    "까지",
    "처럼",
    "에서",
    "으로",
    "그리고",
    "하지만",
    "또한",
    "이번",
    "최근",
    "최신",
    "라는",
    "이용",
    "위해",
    "통한",
}

NOISY_TITLE_HINTS = {
    "로그인",
    "회원가입",
    "이용약관",
    "개인정보",
    "공지사항",
    "문의",
    "faq",
    "홈으로",
    "더 많은",
    "구독",
    "트렌드를 읽는 가장 빠른 방법",
}

EMPHASIS_NOISE_HINTS = {
    "공유",
    "버튼",
    "클릭",
    "링크",
    "생성",
    "완료",
    "차감",
    "횟수",
    "로그인",
    "멤버십",
    "무료",
    "원문",
    "출처",
    "무단",
    "재배포",
    "열람",
    "all rights reserved",
    "함께 읽으면",
    "콘텐츠를",
    "읽어야",
    "보여드릴까요",
    "고구마팜",
}

LOW_SIGNAL_PAGE_TITLES = {
    "고구마팜",
    "wepick",
    "careet",
}


@dataclass
class SourceConfig:
    name: str
    url: str


SOURCE_CONFIGS = [
    SourceConfig(name="wepick", url="https://letter.wepick.kr/original/meme"),
    SourceConfig(name="gogumafarm", url="https://gogumafarm.kr/category/trends/"),
    SourceConfig(name="careet", url="https://www.careet.net/"),
]


class WebMemeCollector:
    def __init__(self, timeout_sec: int = 10):
        self.timeout_sec = timeout_sec
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            }
        )

    def collect(
        self,
        max_articles_per_source: Optional[int] = 15,
        lookback_days: Optional[int] = None,
        include_article_body: bool = True,
    ) -> Dict[str, List[dict]]:
        output: Dict[str, List[dict]] = {}
        cutoff_utc: Optional[datetime] = None
        if lookback_days is not None:
            safe_days = max(0, int(lookback_days))
            cutoff_utc = datetime.now(timezone.utc) - timedelta(days=safe_days)

        per_source_limit: Optional[int] = None
        if max_articles_per_source is not None:
            safe_limit = int(max_articles_per_source)
            if safe_limit > 0:
                per_source_limit = safe_limit

        for source in SOURCE_CONFIGS:
            output[source.name] = self._collect_from_source(
                source,
                per_source_limit,
                cutoff_utc=cutoff_utc,
                include_article_body=include_article_body,
            )
        return output

    def _collect_from_source(
        self,
        source: SourceConfig,
        max_items: Optional[int],
        cutoff_utc: Optional[datetime],
        include_article_body: bool,
    ) -> List[dict]:
        try:
            resp = self.session.get(source.url, timeout=self.timeout_sec)
            resp.raise_for_status()
        except requests.RequestException:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        articles: List[dict] = []

        max_candidates = (max_items * 8) if max_items is not None else None
        candidates = self._extract_candidate_posts_from_listing(source, soup, max_candidates=max_candidates)
        if not candidates:
            fallback_max_candidates = (max_items * 12) if max_items is not None else None
            candidates = self._extract_candidate_posts_from_listing_generic(source, soup, max_candidates=fallback_max_candidates)
        if source.name == "wepick" and not candidates:
            return self._collect_wepick_from_sitemap(max_items=max_items, cutoff_utc=cutoff_utc)

        seen_urls = set()
        for candidate in candidates:
            href = str(candidate.get("url", "")).strip()
            title = str(candidate.get("title", "")).strip()
            if not href or href in seen_urls:
                continue
            if not title:
                title = "article"

            article_text = ""
            article_excerpt = title
            article_published_dt: Optional[datetime] = None
            article_emphasis_text = ""

            published_dt = candidate.get("published_at")

            # Enforce post-by-post crawling: always open detail pages for title/body/emphasis/date backfill.
            article_text, article_excerpt, article_published_dt, article_page_title, article_emphasis_text = self._fetch_article_content(href)
            if article_page_title and len(article_page_title) > len(title):
                title = article_page_title
            if not include_article_body:
                article_text = title
            if not article_text:
                article_text = title
            if not article_excerpt:
                article_excerpt = title
            if self._is_low_signal_page_title(title):
                continue

            if published_dt is None:
                published_dt = article_published_dt

            if cutoff_utc is not None:
                # For rolling-window reports, keep only dated content inside the lookback range.
                if published_dt is not None and published_dt < cutoff_utc:
                    continue

            clean_title = self._clean_text_for_analysis(title)
            clean_excerpt = self._clean_text_for_analysis(article_excerpt)
            clean_body = self._clean_text_for_analysis(article_text)
            clean_emphasis = self._clean_text_for_analysis(article_emphasis_text)

            articles.append(
                {
                    "source": source.name,
                    "title": title,
                    "url": href,
                    "published_at": published_dt.isoformat() if published_dt else "",
                    "excerpt": article_excerpt,
                    "body_text": article_text,
                    "emphasis_text": article_emphasis_text,
                    "clean_title": clean_title,
                    "clean_excerpt": clean_excerpt,
                    "clean_body_text": clean_body,
                    "clean_emphasis_text": clean_emphasis,
                    "tags": [],
                }
            )
            seen_urls.add(href)
            if max_items is not None and len(articles) >= max_items:
                break

        if not articles and source.name != "wepick":
            return self._collect_source_from_sitemap(source, max_items=max_items, cutoff_utc=cutoff_utc)

        return articles

    def _extract_candidate_posts_from_listing(
        self,
        source: SourceConfig,
        soup: BeautifulSoup,
        max_candidates: Optional[int],
    ) -> List[dict]:
        candidates: List[dict] = []
        seen = set()

        selectors_by_source = {
            "wepick": [
                'a[href*="/post/"]',
            ],
            "gogumafarm": [
                "article h2 a[href]",
                "article h3 a[href]",
                ".post-title a[href]",
                ".entry-title a[href]",
                "main a[href]",
            ],
            "careet": [
                "article a[href]",
                "main a[href]",
                "a[href]",
            ],
        }

        selectors = selectors_by_source.get(source.name, ["a[href]"])
        for selector in selectors:
            for anchor in soup.select(selector):
                href = anchor.get("href", "").strip()
                title = anchor.get_text(" ", strip=True)
                if not href:
                    continue

                resolved = urljoin(source.url, href)
                if not resolved.startswith("http"):
                    continue
                if not self._is_valid_article_link(source.name, resolved, title):
                    continue
                if resolved in seen:
                    continue

                published_dt = self._extract_datetime(anchor)
                candidates.append(
                    {
                        "url": resolved,
                        "title": title,
                        "published_at": published_dt,
                    }
                )
                seen.add(resolved)
                if max_candidates is not None and len(candidates) >= max_candidates:
                    return candidates

        return candidates

    def _extract_candidate_posts_from_listing_generic(
        self,
        source: SourceConfig,
        soup: BeautifulSoup,
        max_candidates: Optional[int],
    ) -> List[dict]:
        candidates: List[dict] = []
        seen = set()
        for anchor in soup.select("a[href]"):
            href = anchor.get("href", "").strip()
            title = anchor.get_text(" ", strip=True)
            if not href:
                continue
            resolved = urljoin(source.url, href)
            if not resolved.startswith("http"):
                continue
            if not self._is_valid_article_link(source.name, resolved, title):
                continue
            if resolved in seen:
                continue

            candidates.append(
                {
                    "url": resolved,
                    "title": title,
                    "published_at": self._extract_datetime(anchor),
                }
            )
            seen.add(resolved)
            if max_candidates is not None and len(candidates) >= max_candidates:
                return candidates
        return candidates

    def _extract_datetime(self, node) -> Optional[datetime]:
        candidates = []
        for attr in ("datetime", "title", "data-date"):
            value = node.get(attr)
            if value:
                candidates.append(value)

        # Many list pages include date text near anchors rather than in attributes.
        candidates.append(node.get_text(" ", strip=True))

        parent = node.parent
        if parent is not None:
            candidates.append(parent.get_text(" ", strip=True))

        for value in candidates:
            dt = self._parse_datetime_candidate(value)
            if dt is not None:
                return dt

        return None

    def _fetch_article_content(self, url: str) -> tuple[str, str, Optional[datetime], str, str]:
        try:
            resp = self.session.get(url, timeout=self.timeout_sec)
            resp.raise_for_status()
        except requests.RequestException:
            return "", "", None, "", ""

        soup = BeautifulSoup(resp.text, "html.parser")

        excerpt = ""
        page_title = ""
        og_title = soup.select_one('meta[property="og:title"]')
        if og_title and og_title.get("content"):
            page_title = og_title.get("content", "").strip()
        if not page_title:
            h1 = soup.select_one("h1")
            if h1:
                page_title = h1.get_text(" ", strip=True)
        if not page_title and soup.title:
            page_title = soup.title.get_text(" ", strip=True)

        meta_desc = soup.select_one('meta[name="description"]')
        if meta_desc and meta_desc.get("content"):
            excerpt = meta_desc.get("content", "").strip()
        if not excerpt:
            og_desc = soup.select_one('meta[property="og:description"]')
            if og_desc and og_desc.get("content"):
                excerpt = og_desc.get("content", "").strip()

        paragraphs: List[str] = []
        for p in soup.select("article p, main p, .content p, .post-content p, .entry-content p"):
            text = p.get_text(" ", strip=True)
            if len(text) < 20:
                continue
            if self._is_boilerplate_text(text):
                continue
            paragraphs.append(text)
            if len(paragraphs) >= 20:
                break

        if not paragraphs:
            for p in soup.select("p"):
                text = p.get_text(" ", strip=True)
                if len(text) < 30:
                    continue
                if self._is_boilerplate_text(text):
                    continue
                paragraphs.append(text)
                if len(paragraphs) >= 12:
                    break

        body_text = "\n".join(paragraphs).strip()
        published_dt = self._extract_datetime_from_soup(soup)
        emphasis_terms = self._extract_emphasis_terms_from_soup(soup)
        emphasis_text = " ".join(emphasis_terms)
        return body_text, excerpt, published_dt, page_title, emphasis_text

    def _collect_wepick_from_sitemap(self, max_items: Optional[int], cutoff_utc: Optional[datetime]) -> List[dict]:
        try:
            resp = self.session.get("https://letter.wepick.kr/sitemap.xml", timeout=self.timeout_sec)
            resp.raise_for_status()
        except requests.RequestException:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        candidates: List[tuple[str, Optional[datetime]]] = []
        for url_node in soup.select("url"):
            loc_node = url_node.select_one("loc")
            if not loc_node:
                continue
            loc = (loc_node.get_text(" ", strip=True) or "").strip()
            if "/post/" not in loc:
                continue

            lastmod_node = url_node.select_one("lastmod")
            parsed_lastmod: Optional[datetime] = None
            if lastmod_node:
                parsed_lastmod = self._parse_datetime_candidate(lastmod_node.get_text(" ", strip=True))

            if cutoff_utc is not None and parsed_lastmod is not None and parsed_lastmod < cutoff_utc:
                continue

            candidates.append((loc, parsed_lastmod))

        candidates.sort(key=lambda x: x[1] or datetime(1970, 1, 1, tzinfo=timezone.utc), reverse=True)

        results: List[dict] = []
        seen = set()
        for loc, sitemap_dt in candidates:
            if loc in seen:
                continue
            seen.add(loc)

            article_text, article_excerpt, article_dt, article_title, article_emphasis_text = self._fetch_article_content(loc)
            published_dt = article_dt or sitemap_dt

            if cutoff_utc is not None:
                if published_dt is None or published_dt < cutoff_utc:
                    continue

            title = (article_title or "").strip() or (article_excerpt or "").strip() or "wepick article"
            if not self._is_valid_article_link("wepick", loc, title):
                continue
            if self._is_low_signal_page_title(title):
                continue

            if not article_text:
                article_text = title
            if not article_excerpt:
                article_excerpt = title

            results.append(
                {
                    "source": "wepick",
                    "title": title,
                    "url": loc,
                    "published_at": published_dt.isoformat() if published_dt else "",
                    "excerpt": article_excerpt,
                    "body_text": article_text,
                    "emphasis_text": article_emphasis_text,
                    "clean_title": self._clean_text_for_analysis(title),
                    "clean_excerpt": self._clean_text_for_analysis(article_excerpt),
                    "clean_body_text": self._clean_text_for_analysis(article_text),
                    "clean_emphasis_text": self._clean_text_for_analysis(article_emphasis_text),
                    "tags": [],
                }
            )

            if max_items is not None and len(results) >= max_items:
                break

        return results

    def _collect_source_from_sitemap(self, source: SourceConfig, max_items: Optional[int], cutoff_utc: Optional[datetime]) -> List[dict]:
        parsed_base = urlparse(source.url)
        base = f"{parsed_base.scheme}://{parsed_base.netloc}"
        sitemap_candidates = [
            f"{base}/sitemap.xml",
            f"{base}/sitemap_index.xml",
            f"{base}/wp-sitemap.xml",
        ]

        all_sitemap_urls: List[str] = []
        for sitemap_url in sitemap_candidates:
            all_sitemap_urls.extend(self._collect_sitemap_urls(sitemap_url))

        # Some sitemap indexes point to nested sitemap files. Follow one level.
        expanded_urls: List[str] = []
        for sitemap_url in all_sitemap_urls:
            if sitemap_url.endswith(".xml") and ("sitemap" in sitemap_url):
                expanded_urls.extend(self._collect_sitemap_urls(sitemap_url))

        url_entries: List[tuple[str, Optional[datetime]]] = []
        seen = set()
        for u in all_sitemap_urls + expanded_urls:
            if u in seen:
                continue
            seen.add(u)
            if not u.startswith("http"):
                continue
            if not self._is_valid_article_link(source.name, u, "article"):
                continue
            url_entries.append((u, None))

        results: List[dict] = []
        for loc, sitemap_dt in url_entries:
            article_text, article_excerpt, article_dt, article_title, article_emphasis_text = self._fetch_article_content(loc)
            published_dt = article_dt or sitemap_dt

            if cutoff_utc is not None and published_dt is not None and published_dt < cutoff_utc:
                continue

            title = (article_title or "").strip() or (article_excerpt or "").strip() or "article"
            if not self._is_valid_article_link(source.name, loc, title):
                continue
            if self._is_low_signal_page_title(title):
                continue

            if not article_text:
                article_text = title
            if not article_excerpt:
                article_excerpt = title

            results.append(
                {
                    "source": source.name,
                    "title": title,
                    "url": loc,
                    "published_at": published_dt.isoformat() if published_dt else "",
                    "excerpt": article_excerpt,
                    "body_text": article_text,
                    "emphasis_text": article_emphasis_text,
                    "clean_title": self._clean_text_for_analysis(title),
                    "clean_excerpt": self._clean_text_for_analysis(article_excerpt),
                    "clean_body_text": self._clean_text_for_analysis(article_text),
                    "clean_emphasis_text": self._clean_text_for_analysis(article_emphasis_text),
                    "tags": [],
                }
            )

            if max_items is not None and len(results) >= max_items:
                break

        return results

    def _collect_sitemap_urls(self, sitemap_url: str) -> List[str]:
        try:
            resp = self.session.get(sitemap_url, timeout=self.timeout_sec)
            resp.raise_for_status()
        except requests.RequestException:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        urls: List[str] = []
        for loc in soup.select("loc"):
            text = loc.get_text(" ", strip=True)
            if text:
                urls.append(text)
        return urls

    def _extract_datetime_from_soup(self, soup: BeautifulSoup) -> Optional[datetime]:
        candidates: List[str] = []

        meta_selectors = [
            'meta[property="article:published_time"]',
            'meta[property="og:published_time"]',
            'meta[property="article:modified_time"]',
            'meta[property="og:updated_time"]',
            'meta[name="pubdate"]',
            'meta[name="publish_date"]',
            'meta[itemprop="datePublished"]',
            'meta[itemprop="dateModified"]',
        ]
        for selector in meta_selectors:
            node = soup.select_one(selector)
            if node and node.get("content"):
                candidates.append(str(node.get("content")))

        for time_node in soup.select("time[datetime], time[title], [data-date], [data-datetime]"):
            for attr in ("datetime", "title", "data-date", "data-datetime"):
                value = time_node.get(attr)
                if value:
                    candidates.append(str(value))

        text_blob = soup.get_text(" ", strip=True)
        date_match = re.search(r"20\d{2}[./-]\d{1,2}[./-]\d{1,2}", text_blob)
        if date_match:
            candidates.append(date_match.group(0))

        for value in candidates:
            parsed = self._parse_datetime_candidate(value)
            if parsed is not None:
                return parsed
        return None

    def _is_boilerplate_text(self, text: str) -> bool:
        low = (text or "").lower()
        if not low:
            return True
        boilerplate_hints = (
            "all rights reserved",
            "무단 전재",
            "재배포",
            "출처",
            "로그인",
            "멤버십",
            "이용약관",
            "개인정보",
            "사업자번호",
            "청소년 보호",
        )
        return any(h in low for h in boilerplate_hints)

    def _is_low_signal_page_title(self, title: str) -> bool:
        low = (title or "").strip().lower()
        if not low:
            return True
        if low in LOW_SIGNAL_PAGE_TITLES:
            return True
        if ("고구마팜" in low and len(low) <= 12) or ("careet" in low and len(low) <= 12) or ("wepick" in low and len(low) <= 12):
            return True
        if low.endswith(" 홈") or low.endswith(" home"):
            return True
        return False

    def _extract_emphasis_terms_from_soup(self, soup: BeautifulSoup) -> List[str]:
        selectors = [
            "article p strong",
            "article p b",
            "article p mark",
            "main p strong",
            "main p b",
            "main p mark",
            ".content p strong",
            ".content p b",
            ".content p mark",
            ".post-content p strong",
            ".post-content p b",
            ".post-content p mark",
        ]

        results: List[str] = []
        seen = set()
        for selector in selectors:
            for node in soup.select(selector):
                text = node.get_text(" ", strip=True)
                if not text:
                    continue
                norm = " ".join(text.split())
                if len(norm) < 2 or len(norm) > 40:
                    continue
                low = norm.lower()
                if low in seen:
                    continue
                if any(hint in low for hint in NOISY_TITLE_HINTS):
                    continue
                if any(hint in low for hint in EMPHASIS_NOISE_HINTS):
                    continue
                cleaned = self._clean_text_for_analysis(norm)
                if not cleaned:
                    continue
                if len(cleaned.split()) > 3:
                    continue
                seen.add(low)
                results.append(norm)
                if len(results) >= 30:
                    return results
        return results

    def _is_valid_article_link(self, source_name: str, url: str, title: str) -> bool:
        title_lower = (title or "").strip().lower()
        if not title_lower:
            return False

        for hint in NOISY_TITLE_HINTS:
            if hint in title_lower:
                return False

        parsed = urlparse(url)
        path = (parsed.path or "").strip().rstrip("/")
        if not path:
            return False

        blocked_prefixes = (
            "/tag",
            "/category",
            "/notice",
            "/user",
            "/faq",
            "/qna",
            "/content/curation",
            "/content/curationlist",
        )
        for prefix in blocked_prefixes:
            if path.lower().startswith(prefix):
                return False

        if source_name == "wepick":
            # Keep only article detail pages.
            return "/post/" in path.lower()

        if source_name == "careet":
            # Careet article pages are numeric IDs (e.g., /1930).
            slug = path.lstrip("/")
            return slug.isdigit()

        if source_name == "gogumafarm":
            # Exclude navigational pages and keep slug-like article pages.
            if "/page/" in path.lower():
                return False
            if path.count("/") < 1:
                return False
            return True

        return True

    def _clean_text_for_analysis(self, text: str) -> str:
        tokens = RAW_TOKEN_RE.findall((text or "").lower())
        filtered = [
            token
            for token in tokens
            if token not in SCRAPE_STOPWORDS and not token.isdigit()
        ]
        return " ".join(filtered)

    def _parse_datetime_candidate(self, value: str) -> Optional[datetime]:
        if not value:
            return None

        raw = str(value).strip()
        if not raw:
            return None

        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (TypeError, ValueError):
            pass

        date_match = re.search(r"(20\d{2})[./-](\d{1,2})[./-](\d{1,2})", raw)
        if date_match:
            year, month, day = (int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3)))
            try:
                return datetime(year, month, day, tzinfo=timezone.utc)
            except ValueError:
                pass

        try:
            dt = date_parser.parse(raw, fuzzy=True, yearfirst=True)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError):
            return None
