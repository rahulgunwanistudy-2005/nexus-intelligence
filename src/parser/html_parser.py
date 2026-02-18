"""
Nexus Intelligence - HTML Parser v2
Fixed: Saves parquet files named per-query so cache works correctly.
e.g. data/processed/headphones_20260217_120000.parquet
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import pandas as pd


class AmazonParser:

    def __init__(self):
        self.output_dir = Path("data/processed")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def parse_file(self, html_file: Path, output_key: str = "products", query: str = "") -> Dict[str, Any]:
        """
        Parse HTML file into structured data.

        Args:
            html_file:   Path to the HTML file
            output_key:  Prefix for the output filename (use the search query key)
            query:       Original search query (used for relevance filtering)
        """
        print(f"[PARSE] Parsing: {html_file.name}")

        html_content = html_file.read_text(encoding="utf-8")
        soup = BeautifulSoup(html_content, "html.parser")

        products = self._extract_products(soup, query=query)

        if not products:
            return {"success": False, "error": "No products extracted"}

        df = pd.DataFrame(products).drop_duplicates(subset=["title"])

        filename = self._save(df, output_key)

        print(f"[OK] Extracted {len(df)} products → {filename.name}")
        return {"success": True, "filename": str(filename), "count": len(df)}

    # ── Extraction helpers ────────────────────────────────────────────────────

    # Words that are never meaningful for filtering
    _STOP_WORDS = {
        "for", "with", "and", "the", "a", "an", "in", "on", "of",
        "to", "is", "by", "or", "be", "at", "as", "it", "compatible"
    }

    # Phrases that indicate a product is an accessory/case/cable FOR something,
    # not the thing itself. If the title contains these before the keyword,
    # the product is not the main item.
    _ACCESSORY_SIGNALS = [
        "compatible with", "compatible for", "for apple", "for iphone",
        "for samsung", "case for", "cover for", "cable for",
        "charger for", "charging cable", "charging cord",
        "mfi certified", "mfi-certified",
        "protector", "tempered glass", "screen guard",
    ]

    def _relevance_words(self, query: str) -> list:
        """
        Extract meaningful filter words from the query.
        'apple iPhones' → ['apple', 'iphone']
        'sony headphones' → ['sony', 'headphone']
        """
        words = [w.lower().strip() for w in query.split()]
        words = [w for w in words if w not in self._STOP_WORDS and len(w) > 2]
        # Normalise plurals: "iPhones"→"iphone", "headphones"→"headphone"
        words = [w.rstrip("s") if len(w) > 4 else w for w in words]
        return words

    def _is_relevant(self, title: str, filter_words: list) -> bool:
        """
        Return True only if the title is actually ABOUT the query,
        not just an accessory that mentions the query in a compatibility note.

        Strategy:
        1. All filter words must appear in the title.
        2. The title must NOT start with an accessory signal BEFORE the main keyword.
           e.g. "USB Cable Compatible with iPhone" → rejected
                "iPhone 15 Pro Max 256GB" → accepted
        """
        t = title.lower()

        # Rule 1: all filter words must be present somewhere
        if not all(w in t for w in filter_words):
            return False

        # Rule 2: reject titles that lead with accessory language
        for signal in self._ACCESSORY_SIGNALS:
            if t.startswith(signal):
                return False

        # Rule 3: the FIRST filter word should appear in the first 60 characters
        # "Apple iPhone 15" → "apple" at position 0 [OK]
        # "USB C Cable ... Compatible for Apple iPhone" → "apple" at position 40+ [ERROR]
        first_word = filter_words[0]
        first_pos = t.find(first_word)
        if first_pos > 60:
            return False

        return True

    def _extract_products(self, soup: BeautifulSoup, query: str = "") -> List[Dict[str, Any]]:
        cards = soup.find_all("div", {"data-component-type": "s-search-result"})
        print(f"[SCAN] Found {len(cards)} product cards")

        filter_words = self._relevance_words(query) if query else []
        if filter_words:
            print(f"🎯 Relevance filter words: {filter_words}")

        products = []
        skipped = 0
        for card in cards:
            try:
                p = self._parse_card(card)
                if not p:
                    continue

                if filter_words and not self._is_relevant(p["title"], filter_words):
                    skipped += 1
                    continue

                products.append(p)
            except Exception:
                continue

        print(f"[OK] Kept {len(products)} | [WARN] Skipped {skipped} irrelevant")
        return products

    def _parse_card(self, card) -> Optional[Dict[str, Any]]:
        title = self._title(card)
        if not title:
            return None

        price = self._price(card)
        if price == 0:
            return None

        return {
            "title":      title,
            "price":      price,
            "rating":     self._rating(card),
            "url":        self._url(card),
            "platform":   "Amazon",
            "scraped_at": datetime.now().isoformat(),
        }

    def _title(self, card) -> Optional[str]:
        # 1. Best selector: span inside h2 with the full product title
        span = card.select_one("h2 span.a-text-normal")
        if span:
            t = span.get_text().strip()
            if len(t) > 10:
                return t

        # 2. Try aria-label on the h2 link (Amazon puts full title here)
        a = card.select_one("h2 a")
        if a:
            label = a.get("aria-label", "").strip()
            if len(label) > 10:
                return label
            t = a.get_text().strip()
            if len(t) > 10:
                return t

        # 3. Fallback: image alt text (usually the full product name)
        img = card.select_one("img.s-image")
        if img:
            alt = img.get("alt", "").strip()
            if len(alt) > 10:
                return alt

        return None

    def _price(self, card) -> float:
        # Try the whole-number part first (most reliable)
        whole = card.select_one(".a-price-whole")
        if whole:
            return self._clean_price(whole.get_text())

        # Try the offscreen accessibility price (e.g. "₹3,990.00")
        offscreen = card.select_one(".a-offscreen")
        if offscreen:
            return self._clean_price(offscreen.get_text())

        return 0.0

    def _rating(self, card) -> float:
        tag = (card.select_one("span[aria-label*='star']") or
               card.select_one("i[class*='a-star']"))
        if tag:
            text = tag.get_text() or tag.get("aria-label", "")
            m = re.search(r"(\d+\.?\d*)", text)
            if m:
                return float(m.group(1))
        return 0.0

    def _url(self, card) -> str:
        a = card.select_one("h2 a")
        if a and a.get("href"):
            href = a["href"]
            return href if href.startswith("http") else f"https://www.amazon.in{href}"
        return ""

    def _clean_price(self, text: str) -> float:
        try:
            return float(re.sub(r"[^\d.]", "", text)) or 0.0
        except Exception:
            return 0.0

    def _save(self, df: pd.DataFrame, output_key: str) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"{output_key}_{timestamp}.parquet"
        df.to_parquet(filename, index=False)
        size_kb = filename.stat().st_size / 1024
        print(f"[SAVED] Saved: {filename.name} ({size_kb:.1f} KB)")
        return filename


def main():
    """Entry point — called by the API via subprocess."""
    # API passes these env vars
    input_file = os.getenv("INPUT_FILE")
    output_key = os.getenv("OUTPUT_KEY", "products")
    search_term = os.getenv("SEARCH_TERM", "")

    if input_file:
        html_file = Path(input_file)
    else:
        # Fallback: find the most recent HTML file
        html_files = sorted(Path("data/raw").glob("*.html"), key=lambda f: f.stat().st_mtime)
        if not html_files:
            print("[ERROR] No HTML files found in data/raw/")
            exit(1)
        html_file = html_files[-1]
        print(f"ℹ️  No INPUT_FILE set, using: {html_file.name}")

    # Use search term as output key if not explicitly set
    if output_key == "products" and search_term:
        output_key = search_term.lower().strip().replace(" ", "_")

    parser = AmazonParser()
    result = parser.parse_file(html_file, output_key=output_key, query=search_term)

    if result["success"]:
        print(f"[OK] Parser complete: {result['count']} products")
    else:
        print(f"[ERROR] Parser failed: {result.get('error')}")
        exit(1)


if __name__ == "__main__":
    main()