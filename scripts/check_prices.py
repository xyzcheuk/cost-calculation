#!/usr/bin/env python3
"""Check DSD drainage record plan fees and update the site when they change.

Fetches https://www.dsd.gov.hk/TC/Service_Enquiries/Drainage_Record_Plans/index.html,
extracts the four fees (search, A4, A3, A0), compares them with the PRICES map in
script.js (the single source of truth) and rewrites script.js plus the fee labels
in index.html when they differ.

Usage:
  python scripts/check_prices.py               # fetch, compare, update on change
  python scripts/check_prices.py --check-only  # compare only, never write files

Exit codes: 0 = ok (updated or up to date), non-zero = scraping/parsing failure.
"""

import argparse
import re
import sys
from pathlib import Path

import requests
from lxml import html

PAGE_URL = "https://www.dsd.gov.hk/TC/Service_Enquiries/Drainage_Record_Plans/index.html"

ROOT = Path(__file__).resolve().parent.parent
SCRIPT_JS = ROOT / "script.js"
INDEX_HTML = ROOT / "index.html"

BASE_XPATH = "/html/body/div/div[1]/div[3]/div/div[2]/div[2]/div/div/table[3]/tbody"

# item ids match the keys of PRICES in script.js / input ids in index.html
ITEMS = {
    "item4": {"name": "A0",     "xpath": BASE_XPATH + "/tr[1]/td[2]/strong"},
    "item2": {"name": "A4",     "xpath": BASE_XPATH + "/tr[2]/td[2]/p[1]/strong"},
    "item3": {"name": "A3",     "xpath": BASE_XPATH + "/tr[2]/td[2]/p[2]/strong"},
    "item1": {"name": "search", "xpath": BASE_XPATH + "/tr[2]/td[2]/p[3]/strong"},
}

LABEL_SNIPPETS = {
    "Searching cost for drainage record plans or drawings": "item1",
    "No. of A4 Drawings sold": "item2",
    "No. of A3 Drawings sold": "item3",
    "No. of A0 Drawings sold": "item4",
}

NUMBER_RE = re.compile(r"(\d+(?:\.\d+)?)")
PRICE_KEY_RE = re.compile(r"(item\d):\s*([\d.]+)")
FEE_TEXT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*元")
TOLERANCE = 0.001


def fetch_page():
    headers = {
        "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    }
    resp = requests.get(PAGE_URL, headers=headers, timeout=30)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    return html.fromstring(resp.text)


def parse_xpath(tree, item_id):
    nodes = tree.xpath(ITEMS[item_id]["xpath"])
    if not nodes:
        return None
    match = NUMBER_RE.search(nodes[0].text_content())
    return float(match.group(1)) if match else None


def parse_structural(tree):
    """Fallback if DSD redesigns: collect every <td> <strong> ending in 元,
    document order == [A0, A4, A3, search]."""
    found = []
    for strong in tree.xpath("//td//strong"):
        match = FEE_TEXT_RE.search(strong.text_content())
        if match:
            found.append(float(match.group(1)))
    if len(found) != 4:
        raise ValueError(
            f"structural fallback expected 4 prices, found {len(found)}: {found}")
    return {"item4": found[0], "item2": found[1],
            "item3": found[2], "item1": found[3]}


def scrape_prices(tree):
    scraped = {}
    missing = []
    for item_id, meta in ITEMS.items():
        value = parse_xpath(tree, item_id)
        if value is None:
            missing.append(meta["name"])
        else:
            scraped[item_id] = value
    if missing:
        print(f"XPath parse incomplete ({', '.join(missing)}); "
              f"trying structural fallback ...")
        return parse_structural(tree)
    return scraped


def read_current_prices():
    prices = {m.group(1): float(m.group(2))
              for m in PRICE_KEY_RE.finditer(SCRIPT_JS.read_text(encoding="utf-8"))}
    if set(prices) != set(ITEMS):
        raise ValueError(f"could not parse PRICES from {SCRIPT_JS}: got {prices}")
    return prices


def fmt(value):
    return f"{value:g}"


def update_script_js(changes):
    js = SCRIPT_JS.read_text(encoding="utf-8")

    def repl(match):
        key = match.group(1)
        return f"{key}: {fmt(changes[key])}" if key in changes else match.group(0)

    SCRIPT_JS.write_text(PRICE_KEY_RE.sub(repl, js), encoding="utf-8")


def update_index_html(changes):
    lines = INDEX_HTML.read_text(encoding="utf-8").splitlines(keepends=True)
    for i, line in enumerate(lines):
        for snippet, item_id in LABEL_SNIPPETS.items():
            if snippet in line and item_id in changes:
                lines[i] = re.sub(r"\(\$[\d.]+\)",
                                  f"(${fmt(changes[item_id])})", line, count=1)
                break
    INDEX_HTML.write_text("".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true",
                        help="compare only, do not modify any files")
    args = parser.parse_args()

    tree = fetch_page()
    scraped = scrape_prices(tree)
    current = read_current_prices()

    changes = {}
    for item_id, meta in ITEMS.items():
        old, new = current[item_id], scraped[item_id]
        if abs(new - old) > TOLERANCE:
            changes[item_id] = new
            print(f"{meta['name']} ({item_id}): ${fmt(old)} -> ${fmt(new)}  CHANGED")
        else:
            print(f"{meta['name']} ({item_id}): ${fmt(old)} unchanged")

    if not changes:
        print("All fees up to date.")
        return 0

    if args.check_only:
        print("--check-only: files NOT modified.")
        return 0

    update_script_js(changes)
    update_index_html(changes)
    print(f"Updated script.js and index.html ({len(changes)} fee(s) changed).")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
