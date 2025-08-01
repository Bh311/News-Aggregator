import feedparser
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from functools import lru_cache
from typing import Dict, List

# ----------------------
# Config / Constants
# ----------------------
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    )
}
TIMEOUT = 8  # seconds for HTTP requests

# ----------------------
# Helper – robust top‑image extractor
# ----------------------
@lru_cache(maxsize=256)
def fetch_top_image(url: str) -> str | None:
    """Return the best‑guess hero image for a news article URL.

    Preference order:
    1. newspaper3k Article.top_image (high accuracy)
    2. <meta property="og:image"> fallback
    3. First <img> tag found in <article> or document body

    The result is cached (LRU) to avoid repeated network calls when the
    same URL appears more than once in a session.
    """
    # --- Try newspaper3k first
    try:
        art = Article(url)
        art.download()
        art.parse()
        if art.top_image:
            return art.top_image
    except Exception:
        pass  # fall through to HTML parsing

    # --- Fallback: scrape the page manually
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(resp.text, "html.parser")

        # 1) OpenGraph image
        og_img = soup.find("meta", property="og:image")
        if og_img and og_img.get("content"):
            return og_img["content"].strip()

        # 2) First meaningful <img>
        article_tag = soup.find("article")
        img_tag = (article_tag.find("img") if article_tag else None) or soup.find("img")
        if img_tag and img_tag.get("src"):
            return img_tag["src"].strip()
    except Exception:
        pass

    return None  # No image found

# ----------------------
# RSS + Scraping helpers
# ----------------------

def parse_rss(feed_url: str):
    """Parse an RSS/Atom feed URL into feedparser entries."""
    return feedparser.parse(feed_url).entries


def scrape_website(url: str) -> List[Dict]:
    """Very lightweight scraper used as RSS fallback – extracts <h1>/<h2>/<h3> titles."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.find_all("article")
    except Exception:
        return []

    titles = []
    for art in articles:
        heading = art.find("h1") or art.find("h2") or art.find("h3")
        if heading and heading.text.strip():
            titles.append({"title": heading.text.strip(), "link": url})

    return titles


def collect_rss_feeds(feed_sources: Dict[str, List[str]], max_articles_per_region: int = 10) -> List[Dict]:
    """Aggregate articles from multiple RSS feeds (and fallback scraping).

    Each returned dict has: title, link, summary, source, image (may be None).
    Duplicate (title, link) pairs are filtered, and results are capped per region.
    """
    all_articles: List[Dict] = []
    seen: set[tuple[str, str]] = set()

    for region, urls in feed_sources.items():
        print(f"\n🌐 Fetching from {region.upper()} sources...")
        count = 0

        for feed_url in urls:
            if count >= max_articles_per_region:
                break

            try:
                for entry in parse_rss(feed_url):
                    title = entry.get("title", "No Title")
                    link = entry.get("link", "#")
                    key = (title, link)

                    if key in seen:
                        continue

                    # --- Build the article record
                    article = {
                        "title": title,
                        "link": link,
                        "summary": entry.get("summary", title),
                        "source": region,
                        "image": fetch_top_image(link),  # <-- NEW IMAGE FIELD
                    }

                    all_articles.append(article)
                    seen.add(key)
                    count += 1
                    if count >= max_articles_per_region:
                        break
            except Exception as rss_err:
                print(f"❌ RSS failed for {feed_url} → {rss_err}\n⚠️ Trying scraping…")
                # --- Very lightweight scrape fallback
                for item in scrape_website(feed_url):
                    if count >= max_articles_per_region:
                        break

                    key = (item["title"], item["link"])
                    if key in seen:
                        continue

                    item.update({
                        "source": region,
                        "summary": item["title"],
                        "image": fetch_top_image(item["link"]),
                    })
                    all_articles.append(item)
                    seen.add(key)
                    count += 1

    return all_articles

# ----------------------
# Full‑article details (for article view)
# ----------------------

def extract_article_data(url: str) -> Dict:
    """Download full article text + hero image via newspaper3k with graceful fallback."""
    art = Article(url)
    art.download()
    art.parse()

    return {
        "title": art.title,
        "text": art.text,
        "top_image": art.top_image or fetch_top_image(url),  # ensure we always try fallback
        "summary": art.summary or art.title,
    }
