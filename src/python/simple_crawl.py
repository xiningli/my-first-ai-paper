import asyncio
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from crawl4ai import AsyncWebCrawler, BFSDeepCrawlStrategy, CrawlerRunConfig
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

START_URL = "https://www.nbcnews.com/"
DATA_ROOT = Path("data/corpus")  # repo root data directory
RAW_DIR = DATA_ROOT / "raw" / "nbc"
META_PATH = DATA_ROOT / "meta" / "index.jsonl"

MAX_DEPTH = 2
MAX_PAGES = 200          # cap on saved pages
REQUEST_DELAY = 0.0      # optional politeness delay between yields
BYTE_BUDGET = 10 * 1024 * 1024  # 10 MB
MIN_CHARS = 800


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def append_meta(rec: dict):
    META_PATH.parent.mkdir(parents=True, exist_ok=True)
    rec.setdefault("fetched_at", now_iso())
    with META_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# def strip_links(md: str) -> str:
#         """Remove hyperlinks from markdown, keeping visible anchor text.

#         Rules:
#             1. Convert [text](http://example) -> text
#             2. Convert inline autolinks <http://example> -> (removed entirely)
#             3. Remove bare URLs (http/https) that stand alone or within text.
#         Order matters to avoid partial matches.
#         """
#         import re as _re
#         # 1. [anchor](url)
#         md = _re.sub(r"\[([^\]]+)\]\((?:https?://[^)\s]+)\)", r"\1", md)
#         # 2. <http://...>
#         md = _re.sub(r"<https?://[^>]+>", "", md)
#         # 3. Bare URLs
#         md = _re.sub(r"https?://\S+", "", md)
#         # Collapse extra spaces created by removals
#         md = _re.sub(r"[ \t]{2,}", " ", md)
#         # Trim trailing spaces per line
#         md = "\n".join(line.rstrip() for line in md.splitlines())
#         return md.strip()


async def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    total_bytes = 0
    saved = 0
    seen_urls: set[str] = set()

    cfg = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=MAX_DEPTH,
            include_external=False,
            max_pages=2,  # traversal ceiling; we still stop earlier via MAX_PAGES/BYTE_BUDGET
        ),
        stream=True,  # Enable streaming
        scraping_strategy=LXMLWebScrapingStrategy(),
        remove_overlay_elements=True,
        excluded_selector="shortcuts",
        keep_data_attributes=True,
        keep_attrs=["data-testid"],
        verbose=True,
        word_count_threshold=10,
        excluded_tags=['form', 'header', 'footer', 'nav'],
        exclude_external_links=True,
        exclude_social_media_links=True,
        exclude_domains=["adtrackers.com", "spammynews.org"],
        exclude_social_media_domains=["facebook.com", "twitter.com"],
    )

    try:
        async with AsyncWebCrawler() as crawler:
            async for result in await crawler.arun(
                url=START_URL, 
                config=cfg
            ):

                url = result.url
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                md = (result.markdown or "").strip()
                b = len(md.encode("utf-8"))
                h_url = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
                out_path = RAW_DIR / f"nbc-{h_url}.md"
                if out_path.exists():
                    continue
                out_path.write_text(md, encoding="utf-8")
                content_hash = "sha256:" + hashlib.sha256(md.encode("utf-8")).hexdigest()
                append_meta({
                    "id": content_hash,
                    "category": "nbc",
                    "source": "nbc_politics_bfs_deepcrawl",
                    "url": url,
                    "path_raw": str(out_path),
                    "path_text": str(out_path),
                    "processed_filename": out_path.name,
                    "bytes": b,
                })
                saved += 1
                total_bytes += b
                print(f"[saved] {url} -> {out_path} (saved={saved}, total={total_bytes/1024:.1f} KB)")
                if saved >= MAX_PAGES:
                    print("[info] Page save cap reached; stopping crawl.")
                    break
    except KeyboardInterrupt:
        print("[info] Interrupted by user; shutting down gracefully...")
    except Exception as e:
        print(f"[warn] Crawler error: {e}")

    print(f"Done. Saved {saved} articles, total {total_bytes/1024/1024:.2f} MB; visited {len(seen_urls)} URLs")


if __name__ == "__main__":
    asyncio.run(main())