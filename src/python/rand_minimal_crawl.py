#!/usr/bin/env python3
"""Minimal RAND articles crawler.

Goals:
  * As small & readable as possible
  * No YAML dependency (hard-coded RAND listing URL + regex)
  * Simple query-param pagination until empty page
  * Fetch article pages (basic HTML -> text) — optional crawl4ai if installed
  * Save plain text files under data/rand_minimal/
  * Avoid duplicates by URL hash; no metadata index

Usage:
  python rand_minimal_crawl.py --pages 5 --out data/rand_minimal --word-only

Add --crawl4ai to attempt crawl4ai AsyncWebCrawler extraction (requires install).
"""
from __future__ import annotations
import argparse
import hashlib
import os
import re
import sys
from pathlib import Path
import time

import httpx
from bs4 import BeautifulSoup

TRY_CRAWL4AI = False
try:  # optional
    from crawl4ai import AsyncWebCrawler
    TRY_CRAWL4AI = True
except Exception:  # pragma: no cover
    TRY_CRAWL4AI = False
import asyncio

BASE_LIST_URL = "https://www.rand.org/pubs/articles.html"  # ?page=N appended
LINK_REGEX = re.compile(r"/pubs/articles/.*\.html$")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z\-']+")


def words_only(text: str) -> str:
    return " ".join(m.group(0).lower() for m in WORD_RE.finditer(text))


def clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()
    body = soup.body or soup
    txt = body.get_text(" \n")
    txt = re.sub(r"\r", "\n", txt)
    txt = re.sub(r"\n{2,}", "\n\n", txt)
    txt = re.sub(r"[ \t]+", " ", txt)
    return txt.strip()


def fetch_html(client: httpx.Client, url: str) -> str | None:
    try:
        r = client.get(url, timeout=30, headers={"User-Agent": "minimal-rand-crawler/0.1"})
        if r.status_code == 403:
            r = client.get(url, timeout=30, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": url
            })
        r.raise_for_status()
        return r.text
    except Exception:
        return None


def list_page_urls(pages: int, start: int = 1):
    for p in range(start, start + pages):
        if p == 1:
            yield BASE_LIST_URL  # often page=1 is same as base
        else:
            yield f"{BASE_LIST_URL}?page={p}"


def extract_article_links(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    out: list[str] = []
    from urllib.parse import urljoin
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if LINK_REGEX.search(href):
            out.append(urljoin(BASE_LIST_URL, href))
    # preserve order, remove dups while keeping first occurrence
    seen = set()
    uniq = []
    for u in out:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq

async def crawl4ai_extract(url: str) -> str | None:
    if not TRY_CRAWL4AI:
        return None
    try:
        async with AsyncWebCrawler() as crawler:
            res = await crawler.arun(url=url)
        text = getattr(res, "markdown", None) or getattr(res, "cleaned_html", None)
        if not text:
            return None
        return clean_text(text)
    except Exception:
        return None

async def fetch_article(client: httpx.Client, url: str, use_c4: bool) -> str | None:
    if use_c4 and TRY_CRAWL4AI:
        t = await crawl4ai_extract(url)
        if t:
            return t
    html = fetch_html(client, url)
    if not html:
        return None
    return clean_text(html)

async def run(args):
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    seen_urls_hash = set()
    total = 0
    async_mode = args.crawl4ai and TRY_CRAWL4AI
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as async_client:
        with httpx.Client(follow_redirects=True, timeout=30) as client:
            for page_url in list_page_urls(args.pages, args.start_page):
                html = fetch_html(client, page_url)
                if not html:
                    print(f"[page] {page_url} -> error")
                    continue
                links = extract_article_links(html)
                if not links:
                    print(f"[page] {page_url} -> 0 links (stopping)")
                    break
                print(f"[page] {page_url} links={len(links)}")
                # simple sequential to stay minimal
                for url in links:
                    if total >= args.max_items:
                        break
                    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
                    if h in seen_urls_hash:
                        continue
                    seen_urls_hash.add(h)
                    text = await fetch_article(async_client if async_mode else client, url, async_mode)
                    if not text:
                        print(f"  [skip] {url} (no text)")
                        continue
                    if args.word_only:
                        text = words_only(text)
                    fname = f"rand-{h}.txt"
                    (out_dir / fname).write_text(text, encoding="utf-8")
                    total += 1
                    if args.delay > 0:
                        time.sleep(args.delay)
                if total >= args.max_items:
                    break
    print(f"Done. saved={total}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Minimal RAND articles crawler")
    ap.add_argument("--pages", type=int, default=2, help="Number of listing pages to scan")
    ap.add_argument("--start-page", type=int, default=1)
    ap.add_argument("--max-items", type=int, default=100)
    ap.add_argument("--out", default="data/rand_minimal")
    ap.add_argument("--word-only", action="store_true")
    ap.add_argument("--crawl4ai", action="store_true", help="Use crawl4ai async extraction first if available")
    ap.add_argument("--delay", type=float, default=0.0, help="Sleep seconds between article fetches (politeness)")
    args = ap.parse_args(argv)
    try:
        asyncio.run(run(args))
        return 0
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130

if __name__ == "__main__":
    raise SystemExit(main())
