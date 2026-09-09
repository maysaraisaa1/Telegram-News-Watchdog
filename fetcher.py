"""
fetcher.py - Robust RSS Feeds Fetcher Engine
وكيل الرصد والذكاء الإخباري الشامل (AI & Sports Autonomous Watchdog)
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import time
from typing import Any, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from bs4 import BeautifulSoup
import feedparser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import config


@dataclass
class RawNewsItem:
    """Represents a freshly scraped news item before processing and scoring."""
    title: str
    link: str
    summary: str
    source_name: str
    category: str
    sub_category: str
    published_at: str
    feed_weight: float


class RSSFetcher:
    """Fetches, cleans, and standardizes RSS news entries from multiple sources."""

    def __init__(
        self,
        timeout: int = config.REQUEST_TIMEOUT,
        max_retries: int = config.MAX_RETRIES,
        user_agent: str = config.USER_AGENT,
    ) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept": "application/rss+xml, application/xml, text/xml, application/atom+xml, text/html;q=0.9, */*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        })

        # Configure connection retries with exponential backoff
        retries = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    @staticmethod
    def clean_html(raw_html: str) -> str:
        """Strips HTML tags, tracking pixels, and normalizes whitespaces."""
        if not raw_html:
            return ""
        try:
            soup = BeautifulSoup(raw_html, "html.parser")
            # Remove scripts, styles, and empty tags
            for tag in soup(["script", "style", "figure", "img"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True)
            return " ".join(text.split())
        except Exception:
            return raw_html.strip()

    @staticmethod
    def clean_url(raw_url: str) -> str:
        """Removes common marketing and tracking query parameters (e.g., utm_*, fbclid)."""
        if not raw_url:
            return ""
        try:
            parsed = urlparse(raw_url)
            query_params = parse_qs(parsed.query)
            # Filter out tracking query arguments
            tracking_prefixes = ("utm_", "fbclid", "gclid", "ocid", "ref", "source")
            filtered_params = {
                k: v for k, v in query_params.items()
                if not any(k.lower().startswith(prefix) for prefix in tracking_prefixes)
            }
            new_query = urlencode(filtered_params, doseq=True)
            cleaned = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment,
            ))
            return cleaned.rstrip("/")
        except Exception:
            return raw_url.strip()

    @staticmethod
    def parse_published_date(entry: Any) -> str:
        """Extracts and normalizes the publication date to ISO 8601 UTC format."""
        # Try structured time parsed by feedparser
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                dt = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)
                return dt.isoformat()
            except Exception:
                pass
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            try:
                dt = datetime.fromtimestamp(time.mktime(entry.updated_parsed), tz=timezone.utc)
                return dt.isoformat()
            except Exception:
                pass

        # Fallback to string representation or current timestamp
        date_str = getattr(entry, "published", "") or getattr(entry, "updated", "")
        if date_str:
            return date_str.strip()
        return datetime.now(timezone.utc).isoformat()

    def fetch_feed(self, source: config.RSSFeedSource) -> List[RawNewsItem]:
        """Fetches and parses a single RSS feed source safely."""
        items: List[RawNewsItem] = []
        try:
            response = self.session.get(source.url, timeout=self.timeout)
            if response.status_code != 200:
                print(f"  [!] HTTP {response.status_code} received from {source.name}")
                return []

            parsed = feedparser.parse(response.content)
            if parsed.bozo and not parsed.entries:
                print(f"  [!] Parse warning for {source.name}: {parsed.bozo_exception}")

            for entry in parsed.entries:
                title = getattr(entry, "title", "").strip()
                link = getattr(entry, "link", "").strip()
                if not title or not link:
                    continue

                raw_summary = (
                    getattr(entry, "summary", "")
                    or getattr(entry, "description", "")
                    or ""
                )
                clean_summary = self.clean_html(raw_summary)
                cleaned_link = self.clean_url(link)
                published_iso = self.parse_published_date(entry)

                items.append(
                    RawNewsItem(
                        title=title,
                        link=cleaned_link,
                        summary=clean_summary,
                        source_name=source.name,
                        category=source.category,
                        sub_category=source.sub_category,
                        published_at=published_iso,
                        feed_weight=source.weight,
                    )
                )
        except requests.RequestException as e:
            print(f"  [X] Network error fetching {source.name}: {e}")
        except Exception as e:
            print(f"  [X] Unexpected error processing {source.name}: {e}")

        return items

    def fetch_all(self, sources: Optional[List[config.RSSFeedSource]] = None) -> List[RawNewsItem]:
        """Fetches all feeds sequentially with error isolation."""
        sources_to_fetch = sources or config.ALL_FEEDS
        total_items: List[RawNewsItem] = []

        for source in sources_to_fetch:
            print(f"  -> Scanning: {source.name}...")
            feed_items = self.fetch_feed(source)
            total_items.extend(feed_items)
            print(f"     [OK] Extracted {len(feed_items)} raw items.")

        return total_items
