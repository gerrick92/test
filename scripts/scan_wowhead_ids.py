from __future__ import annotations

import argparse
import re
import sys
import time
from html import unescape
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import EXPANSIONS, ENTITY_TYPES, DEFAULT_RANGES, entity_url, cache_path, load_json, save_json, write_exports

BAD_TITLE_MARKERS = [
    'not found', 'page not found', 'database error', 'error 404', 'search results for',
    'world of warcraft', 'classic world of warcraft', 'tbc classic', 'wotlk classic'
]

TITLE_SUFFIXES = [
    ' - Item - Classic World of Warcraft',
    ' - Quest - Classic World of Warcraft',
    ' - NPC - Classic World of Warcraft',
    ' - Spell - Classic World of Warcraft',
    ' - Object - Classic World of Warcraft',
    ' - Item - TBC Classic',
    ' - Quest - TBC Classic',
    ' - NPC - TBC Classic',
    ' - Spell - TBC Classic',
    ' - Object - TBC Classic',
    ' - Item - WotLK Classic',
    ' - Quest - WotLK Classic',
    ' - NPC - WotLK Classic',
    ' - Spell - WotLK Classic',
    ' - Object - WotLK Classic',
]


def clean_title(title: str) -> str:
    title = unescape((title or '').strip())
    for suffix in TITLE_SUFFIXES:
        if title.endswith(suffix):
            title = title[:-len(suffix)]
    # Generic fallback: first part before " - Type -"
    title = re.sub(r'\s+-\s+(Item|Quest|NPC|Spell|Object|Zone|Faction|Achievement|Title|Currency)\s+-\s+.*$', '', title, flags=re.I)
    return title.strip()


def parse_page(html: str, url: str, expansion: str, entity_type: str, entity_id: int):
    soup = BeautifulSoup(html, 'html.parser')
    title_tag = soup.find('title')
    h1 = soup.find('h1')
    raw_title = ''
    if h1 and h1.get_text(strip=True):
        raw_title = h1.get_text(' ', strip=True)
    elif title_tag:
        raw_title = title_tag.get_text(' ', strip=True)
    name = clean_title(raw_title)

    lower = name.lower()
    if not name or any(m in lower for m in BAD_TITLE_MARKERS):
        return None
    # Avoid accepting database category pages accidentally.
    if name.lower() in {'items','quests','npcs','spells','objects'}:
        return None

    # Lightweight validation: Wowhead page should contain the entity URL form or a data id.
    if f"/{entity_type}={entity_id}" not in html and f"{entity_type}={entity_id}" not in html:
        # Some valid pages render differently, so keep if title looks specific.
        if len(name) < 3:
            return None

    return {
        'expansion': expansion,
        'type': entity_type,
        'id': entity_id,
        'name': name,
        'url': url,
        'source': 'wowhead-id-scan',
        'meta': {},
    }


def main():
    ap = argparse.ArgumentParser(description='Slow/resumable Wowhead ID scanner. Downloads names+IDs into local JSON/CSV.')
    ap.add_argument('--expansion', required=True, choices=sorted(EXPANSIONS))
    ap.add_argument('--type', required=True, choices=sorted(ENTITY_TYPES))
    ap.add_argument('--start', type=int)
    ap.add_argument('--end', type=int)
    ap.add_argument('--delay', type=float, default=0.35, help='Delay between requests. Keep this gentle.')
    ap.add_argument('--flush-every', type=int, default=50)
    ap.add_argument('--timeout', type=float, default=15)
    args = ap.parse_args()

    if args.start is None or args.end is None:
        start, end = DEFAULT_RANGES.get(args.expansion, {}).get(args.type, (1, 10000))
    else:
        start, end = args.start, args.end

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 WoWDatabaseExplorer/1.6 local personal archival tool',
        'Accept-Language': 'en-US,en;q=0.9',
    })

    cpath = cache_path(args.expansion, args.type)
    cache = load_json(cpath, {'checked': [], 'found': []})
    checked = set(int(x) for x in cache.get('checked', []))
    found_rows = {int(r['id']): r for r in cache.get('found', []) if 'id' in r}

    pending_found = []
    processed = 0
    found_count_start = len(found_rows)

    try:
        for entity_id in range(start, end + 1):
            if entity_id in checked:
                continue
            url = entity_url(args.expansion, args.type, entity_id)
            try:
                r = session.get(url, timeout=args.timeout, allow_redirects=True)
                html = r.text or ''
                row = None
                if r.status_code == 200:
                    row = parse_page(html, r.url, args.expansion, args.type, entity_id)
                if row:
                    found_rows[entity_id] = row
                    pending_found.append(row)
                    print(f"FOUND {args.expansion} {args.type} {entity_id}: {row['name']}")
                else:
                    if entity_id % 100 == 0:
                        print(f"checked {entity_id}...")
            except Exception as e:
                print(f"ERROR {entity_id}: {e}")
            finally:
                checked.add(entity_id)
                processed += 1
                if processed % args.flush_every == 0:
                    cache = {'checked': sorted(checked), 'found': sorted(found_rows.values(), key=lambda x: int(x['id']))}
                    save_json(cpath, cache)
                    if pending_found:
                        write_exports(args.expansion, args.type, pending_found)
                        pending_found.clear()
                    print(f"saved cache: checked={len(checked)} found={len(found_rows)}")
                time.sleep(args.delay)
    except KeyboardInterrupt:
        print('\nInterrupted. Saving progress...')
    finally:
        cache = {'checked': sorted(checked), 'found': sorted(found_rows.values(), key=lambda x: int(x['id']))}
        save_json(cpath, cache)
        if pending_found:
            write_exports(args.expansion, args.type, pending_found)
        write_exports(args.expansion, args.type, found_rows.values())
        print(f"Done. checked={len(checked)} found_total={len(found_rows)} new_found={len(found_rows)-found_count_start}")
        print(f"Export: data/exports/{args.expansion}_{args.type}.json")

if __name__ == '__main__':
    main()
