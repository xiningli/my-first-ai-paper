import asyncio
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

START_URL = "https://www.nbcnews.com/politics"
DATA_ROOT = Path("data/corpus")  # repo root data directory
RAW_DIR = DATA_ROOT / "raw" / "nbc"
META_PATH = DATA_ROOT / "meta" / "index.jsonl"

MAX_DEPTH = 3
MAX_PAGES = 200          # max number of pages we will SAVE
MAX_VISITS = 800         # hard cap on total fetch attempts (safety)
REQUEST_DELAY = 0.0      # set to e.g. 0.3 for polite throttling
BYTE_BUDGET = 10 * 1024 * 1024  # 10 MB
MIN_CHARS = 800


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def append_meta(rec: dict):
    META_PATH.parent.mkdir(parents=True, exist_ok=True)
    rec.setdefault("fetched_at", now_iso())
    with META_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


async def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    total_bytes = 0
    saved = 0
    seen_urls: set[str] = set()

    cfg = CrawlerRunConfig(scraping_strategy=LXMLWebScrapingStrategy(), verbose=True)

    frontier = [(START_URL, 0)]  # (url, depth)
    visits = 0
    try:
        async with AsyncWebCrawler() as crawler:
            while frontier and saved < MAX_PAGES and visits < MAX_VISITS:
                url, depth = frontier.pop(0)
                if url in seen_urls or depth > MAX_DEPTH:
                    continue
                if REQUEST_DELAY:
                    await asyncio.sleep(REQUEST_DELAY)
                try:
                    result = await crawler.arun(url=url, crawler_run_config=cfg)
                except Exception as e:
                    print(f"[error] fetch {url}: {e}")
                    seen_urls.add(url)
                    continue
                visits += 1
                seen_urls.add(url)
                if not result or getattr(result, 'error', None):
                    continue
                md = (result.markdown or "").strip()
                if md and len(md) >= MIN_CHARS:
                    b = len(md.encode("utf-8"))
                    if total_bytes + b > BYTE_BUDGET:
                        print("[info] Byte budget reached; stopping crawl.")
                        break
                    h_url = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
                    out_path = RAW_DIR / f"nbc-{h_url}.md"
                    if not out_path.exists():
                        out_path.write_text(md, encoding="utf-8")
                        content_hash = "sha256:" + hashlib.sha256(md.encode("utf-8")).hexdigest()
                        append_meta({
                            "id": content_hash,
                            "category": "nbc",
                            "source": "nbc_politics_bfs_manual",
                            "url": url,
                            "path_raw": str(out_path),
                            "path_text": str(out_path),
                            "processed_filename": out_path.name,
                            "bytes": b,
                        })
                        saved += 1
                        total_bytes += b
                        print(f"[saved] {url} -> {out_path} (saved={saved}, total={total_bytes/1024:.1f} KB)")
                # enqueue links for BFS
                links = []
                if hasattr(result, 'all_links') and result.all_links:
                    try:
                        links = [l.url for l in result.all_links if getattr(l, 'url', '').startswith(START_URL)]
                    except Exception:
                        links = []
                elif getattr(result, 'html', None):
                    import re as _re
                    for m in _re.finditer(r'href=["\'](.*?)["\']', result.html):
                        href = m.group(1)
                        if href.startswith('/'):
                            href = 'https://www.nbcnews.com' + href
                        if href.startswith(START_URL):
                            links.append(href)
                for nxt in links:
                    if nxt not in seen_urls and all(nxt != u for u, _ in frontier):
                        frontier.append((nxt, depth + 1))
    except KeyboardInterrupt:
        print("[info] Interrupted by user; shutting down gracefully...")
    except Exception as e:
        print(f"[warn] Crawler error during loop/close: {e}")

    print(f"Done. Saved {saved} articles, total {total_bytes/1024/1024:.2f} MB; visited {len(seen_urls)} URLs (attempted {visits})")


if __name__ == "__main__":
    asyncio.run(main())