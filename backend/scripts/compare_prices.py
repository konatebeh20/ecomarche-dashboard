#!/usr/bin/env python3
"""Compare backend product prices with prices present in the dataset CSV.

Usage: python compare_prices.py

Prints a table with: product_id, product_name, backend_price, dataset_most_common_price, dataset_price_samples
"""
import csv
import requests
import os
import difflib
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(__file__))
CSV_PATH = os.path.join(ROOT, 'asstes', 'data', 'supermarche_historique_ventes.csv')
API_URL = 'http://127.0.0.1:8000/api/produits/all'


def load_backend_products():
    try:
        r = requests.get(API_URL, timeout=10)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and data.get('produits'):
            return data['produits']
        if isinstance(data, list):
            return data
        # try nested
        return []
    except Exception as e:
        print('Error fetching backend products:', e)
        return []


def build_csv_index():
    """Return (name_list, price_index) where price_index[name] is list of prices found for that name."""
    price_index = defaultdict(list)
    name_list = []
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # detect likely columns
        name_col = None
        price_col = None
        for h in reader.fieldnames:
            lh = h.lower()
            if not name_col and ('product_name' == lh or 'product' == lh or 'product_name' in lh):
                name_col = h
            if not price_col and ('unit_price' == lh or 'unitprice' == lh or 'unit_price' in lh or 'prix' in lh):
                price_col = h
        if not name_col:
            name_col = reader.fieldnames[2] if len(reader.fieldnames) > 2 else reader.fieldnames[0]
        for row in reader:
            name = (row.get(name_col) or '').strip()
            if not name:
                continue
            if name not in price_index:
                name_list.append(name)
            price_raw = (row.get(price_col) or '').strip() if price_col else ''
            price = None
            try:
                if price_raw:
                    price = float(price_raw)
            except Exception:
                p = price_raw.replace(' ', '').replace(',', '.')
                try:
                    price = float(p)
                except Exception:
                    price = None
            if price is not None:
                price_index[name].append(price)
    return name_list, price_index


def scan_csv_for_prices(product_names):
    # Build index of dataset names -> prices, then fuzzy-match backend names to dataset names
    name_list, price_index = build_csv_index()
    mapping = {}
    for pname in product_names:
        pname_l = pname or ''
        # exact
        if pname in price_index:
            mapping[pname_l] = price_index[pname]
            continue
        # case-insensitive exact
        found = None
        for n in price_index.keys():
            if n.lower() == pname_l.lower():
                found = n
                break
        if found:
            mapping[pname_l] = price_index[found]
            continue
        # fuzzy match best candidate from name_list
        candidates = difflib.get_close_matches(pname_l, name_list, n=1, cutoff=0.6)
        if candidates:
            best = candidates[0]
            mapping[pname_l] = price_index.get(best, [])
        else:
            # try substring heuristics
            matches = [n for n in name_list if pname_l.lower() in n.lower() or n.lower() in pname_l.lower()]
            if matches:
                mapping[pname_l] = price_index.get(matches[0], [])
            else:
                mapping[pname_l] = []
    return mapping


def summarize(mapping):
    out = {}
    for name, prices in mapping.items():
        if not prices:
            out[name] = {'most_common': None, 'samples': []}
            continue
        c = Counter(prices)
        most_common, count = c.most_common(1)[0]
        samples = sorted(list(set(prices)))[:5]
        out[name] = {'most_common': most_common, 'samples': samples, 'count': len(prices)}
    return out


def main():
    products = load_backend_products()
    if not products:
        print('No products found from backend API; aborting.')
        return

    names = [p.get('nom') for p in products if p.get('nom')]
    csv_mapping = scan_csv_for_prices(names)
    summary = summarize(csv_mapping)

    print('\nComparison product prices (backend vs dataset):\n')
    print('id\tname\tbackend_price\tdataset_most_common\tdataset_samples\tdataset_count')
    for p in products:
        pid = p.get('id')
        name = p.get('nom')
        backend_price = p.get('prix_unitaire')
        key = name.lower() if name else name
        info = summary.get(key) or summary.get(name) or {'most_common': None, 'samples': []}
        most = info.get('most_common')
        samples = info.get('samples')
        count = info.get('count') or 0
        print(f"{pid}\t{name}\t{backend_price}\t{most}\t{samples}\t{count}")


if __name__ == '__main__':
    main()
