"""
Crawler: SLINTEC Sri Lanka — Ready-to-go Technologies
https://www.slintec.lk/what-we-offer/ready-to-go-technologies/

Single static page. Each technology is an <h2> heading followed by
description paragraphs/lists.

Run from the apctt-gateway directory:
    python scripts/crawl_slintec.py

Requirements: httpx, beautifulsoup4
"""

import asyncio
import json
import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup, NavigableString

PAGE_URL = "https://www.slintec.lk/what-we-offer/ready-to-go-technologies/"
OUT_PATH = Path(__file__).parent.parent / "backend" / "sources" / "data" / "slintec.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; APCTT-Gateway-Crawler/1.0)",
    "Accept": "text/html,application/xhtml+xml",
}

# Headings that are page structure, not technology names
SKIP_TITLES = {
    "ready-to-go technologies", "what we offer", "contact us", "get in touch",
    "our technologies", "technologies", "home", "about", "services", "news",
}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:50]


def _detect_sector(text: str) -> str:
    mapping = [
        ("Agriculture", ["agri", "fertiliz", "seed", "crop", "plant", "fungicide", "herbicide", "coconut"]),
        ("Health", ["wound", "antimicrobial", "antibacterial", "medic", "nutraceutical", "honey", "herbal"]),
        ("Food", ["food", "nutrition", "wash", "beverage", "packaging"]),
        ("Environment", ["water filtration", "water treat", "waste", "recycl", "oil water", "hydrophobic"]),
        ("Energy", ["energy", "solar", "battery", "fuel"]),
        ("Materials", ["nano", "graphene", "coating", "composite", "textile", "fabric", "rubber",
                       "polymer", "corrosion", "lubricant", "paint", "glass"]),
        ("ICT", ["software", "digital", "sensor", "iot", "monitoring"]),
    ]
    low = text.lower()
    for sector, keywords in mapping:
        if any(k in low for k in keywords):
            return sector
    return "Technology"


def parse_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    # Find the main content area — try common WordPress selectors, fall back to body
    content = (
        soup.select_one(".entry-content")
        or soup.select_one(".post-content")
        or soup.select_one("article")
        or soup.select_one("main")
        or soup.body
    )

    # Gather all h2 elements inside content
    headings = content.find_all("h2")

    records = []
    for h in headings:
        title = h.get_text(strip=True)
        # Skip page-structure headings
        if not title or title.lower() in SKIP_TITLES or len(title) < 4:
            continue

        # Collect text from sibling elements until the next h2
        text_parts = []
        for sib in h.find_next_siblings():
            if sib.name == "h2":
                break
            if isinstance(sib, NavigableString):
                continue
            t = sib.get_text(" ", strip=True)
            if t and len(t) > 10:
                text_parts.append(t)

        summary = " ".join(text_parts[:4])

        # Strip contact boilerplate from summary
        summary = re.sub(
            r"(Contact|For more|Inquiries|Email|Phone|Tel|interested)[^\n]{0,200}", "",
            summary, flags=re.IGNORECASE,
        ).strip()

        slug = _slug(title)
        sector = _detect_sector(title + " " + summary)
        stop = {"and", "the", "for", "with", "from", "into", "using", "based", "that", "this"}
        keywords = [w for w in re.split(r"\W+", title.lower()) if len(w) > 3 and w not in stop]

        records.append({
            "id": f"slintec_{slug}",
            "tech_id": slug,
            "title": title,
            "summary": summary[:800],
            "institute": "SLINTEC",
            "trl": "",
            "sector": sector,
            "keywords": keywords[:10],
            "url": PAGE_URL,
        })

    return records


async def main():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        print(f"Fetching {PAGE_URL} ...")
        r = await client.get(PAGE_URL, headers=HEADERS, timeout=30)
        r.raise_for_status()

    records = parse_page(r.text)

    # Deduplicate by id
    seen, unique = set(), []
    for rec in records:
        if rec["id"] not in seen:
            seen.add(rec["id"])
            unique.append(rec)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)

    print(f"\nDone. {len(unique)} technologies saved to {OUT_PATH}")
    for rec in unique:
        print(f"  • [{rec['sector']}] {rec['title'][:70]}")


if __name__ == "__main__":
    asyncio.run(main())
