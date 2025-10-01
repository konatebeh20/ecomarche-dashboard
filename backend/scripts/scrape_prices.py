"""Simple scraper to look up product prices on Auchan and Jumia.

Usage:
  python scrape_prices.py --dry-run --products "Pommes Golden,Tomates,Bananes"

This script is intentionally conservative: it does not write to the DB by default.
It will read `backend/asstes/data/supermarche_historique_ventes.csv`, try to match product
names and produce `backend/asstes/data/supermarche_historique_ventes.prix_detecte.csv` with
an additional `prix_detecte` column (first price found via search heuristics).

Notes:
- Scraping public websites may be subject to terms of use. Use responsibly.
- Matching is fuzzy and based on lowercase substring checks; adjust mapping rules for
  your catalog if needed.
"""
import argparse
import csv
import os
import re
import time
from urllib.parse import quote_plus
import difflib

import requests
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_CSV = os.path.join(ROOT, 'asstes', 'data', 'supermarche_historique_ventes.csv')
OUT_CSV = os.path.join(ROOT, 'asstes', 'data', 'supermarche_historique_ventes.prix_detecte.csv')

HEADERS = {
    'User-Agent': 'price-scraper-bot/1.0 (+https://example.com)'
}

AUCHAN_SEARCH = 'https://www.auchan.ci/search?query={q}'
JUMIA_SEARCH = 'https://www.jumia.ci/catalog/?q={q}'

# simple regex to find FCFA-like prices in text
PRICE_RGX = re.compile(r"(\d[0-9\s\,]*\d)\s*FCFA", re.IGNORECASE)
NUM_RGX = re.compile(r"[0-9]+(?:[\s,][0-9]{3})*(?:\.[0-9]+)?")

# regex to detect unit hints near a price (kg, g, pièce, pack)
UNIT_RGX = re.compile(r"(\d[0-9\s\,]*\d)\s*FCFA\s*(?:/|par)?\s*(kg|g|pi[eè]ce|pcs?|pack|unité|u)\b", re.IGNORECASE)


def extract_price_from_text(text):
    if not text:
        return None, None
    # try to find a price with an adjacent unit
    um = UNIT_RGX.search(text)
    if um:
        num = um.group(1)
        unit = um.group(2)
        num = num.replace(' ', '').replace(',', '')
        try:
            return float(num), unit.lower()
        except Exception:
            pass
    m = PRICE_RGX.search(text)
    if m:
        num = m.group(1)
        num = num.replace(' ', '').replace(',', '')
        try:
            return float(num), None
        except Exception:
            return None, None
    # fallback: find any number and assume FCFA
    m2 = NUM_RGX.search(text)
    if m2:
        try:
            return float(m2.group(0).replace(' ', '').replace(',', '')), None
        except Exception:
            return None, None
    return None, None


def search_auchan(product_name):
    q = quote_plus(product_name)
    url = AUCHAN_SEARCH.format(q=q)
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
    except Exception:
        return None, None, url
    soup = BeautifulSoup(r.text, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    price, unit = extract_price_from_text(text)
    return price, unit, url


def search_jumia(product_name):
    q = quote_plus(product_name)
    url = JUMIA_SEARCH.format(q=q)
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
    except Exception:
        return None, None, url
    soup = BeautifulSoup(r.text, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    price, unit = extract_price_from_text(text)
    return price, unit, url


def find_price_for_product(product_name):
    # heuristics: try Auchan first, then Jumia
    price, unit, source = search_auchan(product_name)
    if price:
        return price, unit, source
    time.sleep(0.5)
    price, unit, source = search_jumia(product_name)
    return price, unit, source


def run_dry_run(sample_products=None, limit=2000):
    # read CSV header and sample unique product names
    seen = {}
    with open(DATA_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            name = row.get('Product_Name') or row.get('Product') or ''
            name = name.strip()
            if name and name not in seen:
                seen[name] = None
            if len(seen) >= (limit if sample_products is None else len(sample_products)):
                break
    product_list = sample_products if sample_products else list(seen.keys())[:50]

    results = {}
    for name in product_list:
        print(f"Looking up: {name}")
        price, unit, url = find_price_for_product(name)
        results[name] = {'price': price, 'unit': unit, 'url': url}
        hint = f"{price}" if price is not None else 'None'
        if unit:
            hint += f" (unit: {unit})"
        print(f"  => {hint} (source: {url})")
        time.sleep(1)
    return results


def _best_match_name(name, choices, cutoff=0.6):
    # return best fuzzy match or None
    if not name:
        return None
    best = difflib.get_close_matches(name, choices, n=1, cutoff=cutoff)
    return best[0] if best else None


def write_detected_prices(results, out_csv=OUT_CSV, max_price=100000.0, cutoff=0.6):
    # create mapping product_name -> detected info
    mapping = results
    with open(DATA_CSV, newline='', encoding='utf-8') as inf, open(out_csv, 'w', newline='', encoding='utf-8') as outf:
        reader = csv.DictReader(inf)
        fieldnames = list(reader.fieldnames) + ['prix_detecte', 'unite_detectee', 'source_url']
        writer = csv.DictWriter(outf, fieldnames=fieldnames)
        writer.writeheader()

        # build set of product names present in CSV for fuzzy matching
        all_names = []
        inf.seek(0)
        _reader2 = csv.DictReader(inf)
        for r in _reader2:
            nm = (r.get('Product_Name') or r.get('Product') or '').strip()
            if nm:
                all_names.append(nm)

        # iterate original rows and attach detected price via exact or fuzzy match
        inf.seek(0)
        reader = csv.DictReader(inf)
        for row in reader:
            name = (row.get('Product_Name') or row.get('Product') or '').strip()
            detected_price = ''
            detected_unit = ''
            source = ''

            # try exact match first
            if name in mapping and mapping[name]['price'] is not None:
                p = mapping[name]['price']
                u = mapping[name].get('unit')
                if p and 0 < p <= max_price:
                    detected_price = p
                    detected_unit = u or ''
                    source = mapping[name].get('url') or ''
            else:
                # fuzzy match: find a key from mapping that matches this row's name
                candidates = list(mapping.keys())
                match = _best_match_name(name, candidates, cutoff=cutoff)
                if match:
                    p = mapping[match]['price']
                    u = mapping[match].get('unit')
                    if p and 0 < p <= max_price:
                        detected_price = p
                        detected_unit = u or ''
                        source = mapping[match].get('url') or ''

            row['prix_detecte'] = detected_price
            row['unite_detectee'] = detected_unit
            row['source_url'] = source
            writer.writerow(row)
    print('Wrote', out_csv)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Do not write DB, only show detected prices')
    parser.add_argument('--products', type=str, help='Comma separated product names to search')
    parser.add_argument('--out-csv', type=str, default=OUT_CSV, help='Output CSV path for detected prices')
    parser.add_argument('--max-price', type=float, default=100000.0, help='Maximum plausible price (FCFA) to accept')
    parser.add_argument('--cutoff', type=float, default=0.65, help='Fuzzy match cutoff (0-1) when mapping names')
    args = parser.parse_args()

    sample_products = None
    if args.products:
        sample_products = [p.strip() for p in args.products.split(',') if p.strip()]

    results = run_dry_run(sample_products=sample_products)
    if args.dry_run:
        print('\nDry run results:')
        for k, v in results.items():
            print(f"{k} -> {v['price']} (source: {v['url']})")
        return

    write_detected_prices(results, out_csv=args.out_csv, max_price=args.max_price, cutoff=args.cutoff)


if __name__ == '__main__':
    main()
