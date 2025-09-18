import asyncio
from crawl4ai import AsyncWebCrawler
from pathlib import Path
import re
import hashlib
from bs4 import BeautifulSoup

TARGET_URL = "https://www.nbcnews.com/business"
RAW_DIR = Path("data/corpus/raw/nbc")
PROC_DIR = Path("data/corpus/processed/nbc")
META_PATH = Path("data/corpus/meta/index.jsonl")

def normalize_text(t: str) -> str:
    t = re.sub(r"\r", "\n", t)
    t = re.sub(r"\n{2,}", "\n\n", t)
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()

def append_meta(rec: dict):
    META_PATH.parent.mkdir(parents=True, exist_ok=True)
    with META_PATH.open("a", encoding="utf-8") as f:
        import json, datetime
        rec.setdefault("fetched_at", datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z")
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

async def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROC_DIR.mkdir(parents=True, exist_ok=True)
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=TARGET_URL)
        md = result.markdown or ""
        # Derive simple cleaned plain text from markdown via BeautifulSoup as a quick approximation
        # soup = BeautifulSoup(md, "lxml")
        # text = normalize_text(soup.get_text(" \n"))
        # Hash for filename uniqueness
        h = hashlib.sha256(TARGET_URL.encode("utf-8")).hexdigest()[:16]
        raw_path = RAW_DIR / f"nbc-{h}.md"
        proc_path = PROC_DIR / f"nbc-{h}.txt"
        raw_path.write_text(md, encoding="utf-8")
        # proc_path.write_text(text, encoding="utf-8")
        append_meta({
            "id": "sha256:" + hashlib.sha256(md.encode("utf-8")).hexdigest(),
            "category": "nbc",  # simple ad-hoc category
            "source": "nbc_business_frontpage",
            "url": TARGET_URL,
            "path_raw": str(raw_path),
            "path_text": str(proc_path),
            "processed_filename": proc_path.name,
            # "content_type": "text/markdown",
            # "bytes": len(md.encode("utf-8")),
            # "status": "ok",
            # "error": None,
            # "title": None,
            # "published_date": None,
        })
        print(f"Saved markdown -> {raw_path}\nSaved text -> {proc_path}")

if __name__ == "__main__":
    asyncio.run(main())