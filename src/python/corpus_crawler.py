#!/usr/bin/env python3
"""Corpus crawler using crawl4ai framework.

Features:
  * Reads YAML sources config (categories -> sources)
  * Supports selecting categories and sources
  * For each source: RSS (TODO: simple fetch) or HTML index + pagination
  * Uses crawl4ai to fetch & extract cleaned text
  * Stores raw HTML and processed plain text (word-only optional)
  * Appends metadata to data/corpus/meta/index.jsonl

Limitations:
  * Simplified RSS (could reuse feedparser if needed)
  * PDF extraction not yet implemented here
  * Concurrency serial for simplicity (crawl4ai can manage concurrency if extended)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

try:
    from crawl4ai import WebCrawler
except Exception:  # pragma: no cover
    WebCrawler = None  # type: ignore

import yaml
from bs4 import BeautifulSoup
import httpx

RAW_DIR = Path("data/corpus/raw")
PROC_DIR = Path("data/corpus/processed")
META_DIR = Path("data/corpus/meta")
INDEX_PATH = META_DIR / "index.jsonl"
WORD_RE = re.compile(r"[A-Za-z][A-Za-z\-']+")


def words_only(text: str) -> str:
    return " ".join(m.group(0).lower() for m in WORD_RE.finditer(text))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_config(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_paginated_urls(base_url: str, paginate: Dict[str, Any], exhaust: bool, max_index: int) -> Iterable[str]:
    if not paginate:
        yield base_url
        return
    mode = paginate.get("mode", "query")
    if mode != "query":
        yield base_url
        return
    param = paginate.get("param", "page")
    start = int(paginate.get("start", 1))
    max_pages = int(paginate.get("max_pages", 1))
    stop_on_empty = bool(paginate.get("stop_on_empty", True))
    page = start
    fetched_any = False
    while True:
        if not exhaust and page >= start + max_pages:
            break
        if exhaust and not fetched_any and page >= start + max_pages:
            # allow going beyond configured max_pages when exhaust
            pass
        if not exhaust and page >= start + max_pages:
            break
        if "?" in base_url:
            url = f"{base_url}&{param}={page}"
        else:
            url = f"{base_url}?{param}={page}"
        yield url
        page += 1
        if not exhaust and page >= start + max_pages:
            break
        if exhaust and stop_on_empty and fetched_any and page > start + max_pages * 50:
            # safety guard: don't loop forever
            break
        # upstream logic will stop when a page yields zero new links


def extract_index_links(html: str, base_url: str, pattern: str, max_links: int) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "lxml")
    rx = re.compile(pattern)
    found: List[Dict[str, str]] = []
    from urllib.parse import urljoin
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not rx.search(href):
            continue
        full = urljoin(base_url, href)
        title = a.get_text(strip=True) or None
        found.append({"url": full, "title": title})
        if len(found) >= max_links:
            break
    return found


def append_index(rec: Dict[str, Any]) -> None:
    META_DIR.mkdir(parents=True, exist_ok=True)
    with INDEX_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def hash_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_text(t: str) -> str:
    t = t.replace("\r", "\n")
    t = re.sub(r"\n{2,}", "\n\n", t)
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()


def fetch_html(client: httpx.Client, url: str, ua: str) -> Optional[str]:
    try:
        r = client.get(url, headers={"User-Agent": ua}, timeout=30)
        if r.status_code == 403:
            r = client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": url
            }, timeout=30)
        r.raise_for_status()
        return r.text
    except Exception:
        return None


def crawl_article(crawler: Any, url: str) -> Optional[str]:
    if crawler is None:
        return None
    try:
        result = crawler.run(url)
        # crawl4ai returns structured output; assume result.markdown or result.cleaned_html
        text = getattr(result, "markdown", None) or getattr(result, "cleaned_html", None)
        if not text:
            return None
        return normalize_text(BeautifulSoup(text, "lxml").get_text(" \n"))
    except Exception:
        return None


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Corpus crawler using crawl4ai")
    ap.add_argument("--config", default="data/corpus/sources.yaml")
    ap.add_argument("--categories", nargs="*")
    ap.add_argument("--sources", nargs="*")
    ap.add_argument("--target-bytes", type=int, default=20_000_000_000)
    ap.add_argument("--max-items", type=int, default=100000)
    ap.add_argument("--user-agent", default="policy-corpus-crawl4ai/0.1")
    ap.add_argument("--word-only", action="store_true")
    ap.add_argument("--validate-sources", action="store_true")
    ap.add_argument("--exhaust-pagination", action="store_true")
    args = ap.parse_args(argv)

    cfg_path = Path(args.config)
    try:
        cfg = load_config(cfg_path)
    except Exception as e:
        print(f"[error] load config: {e}", file=sys.stderr)
        return 1

    categories = cfg.get("categories", {})
    sel_cats = set(args.categories or [])
    sel_srcs = set(args.sources or [])

    crawler = None
    if WebCrawler is not None and not args.validate_sources:
        try:
            crawler = WebCrawler()
        except Exception:
            crawler = None

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROC_DIR.mkdir(parents=True, exist_ok=True)
    META_DIR.mkdir(parents=True, exist_ok=True)

    total_bytes = 0
    ok_count = 0
    seen_hash: set[str] = set()

    with httpx.Client(follow_redirects=True) as client:
        for cat_name, cat_data in categories.items():
            if sel_cats and cat_name not in sel_cats:
                continue
            sources = (cat_data or {}).get("sources", [])
            for src in sources:
                key = src.get("key")
                if sel_srcs and key not in sel_srcs:
                    continue
                if not src.get("enabled", True):
                    continue
                print(f"[source] {cat_name}/{key}")
                items: List[Dict[str, Any]] = []
                # For now skip RSS (future: implement feed fetch)
                if not items:
                    index_url = src.get("html_index")
                    link_regex = src.get("link_regex")
                    max_index = int(src.get("max_index", 50))
                    paginate = src.get("paginate") or {}
                    if index_url and link_regex:
                        collected: List[Dict[str, str]] = []
                        for page_url in build_paginated_urls(index_url, paginate, args.exhaust_pagination, max_index):
                            html = fetch_html(client, page_url, args.user_agent)
                            if html is None:
                                continue
                            links = extract_index_links(html, page_url, link_regex, max_index - len(collected))
                            if not links and not collected:
                                # first page no links -> break
                                break
                            if not links:
                                break
                            collected.extend(links)
                            print(f"  [page] {page_url} links={len(links)} total={len(collected)}")
                            if len(collected) >= max_index:
                                break
                        if collected:
                            append_index({
                                "id": None,
                                "category": cat_name,
                                "source": key,
                                "url": index_url,
                                "status": "info",
                                "error": f"html-fallback: {len(collected)} items",
                                "fetched_at": now_iso(),
                            })
                            for li in collected:
                                items.append({"url": li["url"], "title": li.get("title"), "pub_date": None})
                if args.validate_sources:
                    continue
                for it in items:
                    if total_bytes >= args.target_bytes or ok_count >= args.max_items:
                        break
                    url = it["url"]
                    text = crawl_article(crawler, url)
                    # Fallback simple fetch if crawler unavailable or returned nothing
                    if not text:
                        html = fetch_html(client, url, args.user_agent)
                        if html:
                            text = normalize_text(BeautifulSoup(html, "lxml").get_text(" \n"))
                    if not text:
                        append_index({
                            "id": None,
                            "category": cat_name,
                            "source": key,
                            "url": url,
                            "status": "error",
                            "error": "no-text",
                            "fetched_at": now_iso(),
                        })
                        continue
                    if args.word_only:
                        text = words_only(text)
                    h = hash_text(text)
                    if h in seen_hash:
                        append_index({
                            "id": h,
                            "category": cat_name,
                            "source": key,
                            "url": url,
                            "status": "duplicate",
                            "error": None,
                            "fetched_at": now_iso(),
                        })
                        continue
                    seen_hash.add(h)
                    safe = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
                    raw_dir = RAW_DIR / cat_name / key
                    proc_dir = PROC_DIR / cat_name / key
                    raw_dir.mkdir(parents=True, exist_ok=True)
                    proc_dir.mkdir(parents=True, exist_ok=True)
                    # raw html already fetched only in fallback path; skip writing raw to keep simple
                    proc_path = proc_dir / f"{cat_name}-{key}-{safe}.txt"
                    proc_path.write_text(text, encoding="utf-8")
                    size = len(text.encode("utf-8"))
                    total_bytes += size
                    ok_count += 1
                    append_index({
                        "id": h,
                        "category": cat_name,
                        "source": key,
                        "url": url,
                        "path_raw": None,
                        "path_text": str(proc_path),
                        "processed_filename": proc_path.name,
                        "content_type": "text/plain",
                        "bytes": size,
                        "fetched_at": now_iso(),
                        "title": it.get("title"),
                        "published_date": it.get("pub_date"),
                        "status": "ok",
                        "error": None,
                    })
        return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
