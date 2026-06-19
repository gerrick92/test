from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import write_exports, URL_PREFIX

# Fast paths. These are listview pages and may still cap at 1000.
SAMPLE_TARGETS = [
    ('classic','quest','/quests'),
    ('classic','item','/items'),
    ('classic','npc','/npcs'),
    ('classic','spell','/spells'),
]

FULL_TARGETS = []
for exp in ('classic','tbc','wotlk'):
    for typ, paths in {
        'quest': ['/quests','/quests/eastern-kingdoms','/quests/kalimdor','/quests/dungeons','/quests/raids','/quests/classes','/quests/professions','/quests/battlegrounds'],
        'item': ['/items','/items/armor','/items/weapons','/items/consumables','/items/containers','/items/trade-goods','/items/projectiles','/items/quest','/items/keys','/items/miscellaneous','/items/recipes','/items/item-enhancements'],
        'npc': ['/npcs'],
        'spell': ['/spells','/spells/class-skills','/spells/professions','/spells/secondary-skills','/spells/npc-abilities','/spells/buffs'],
        'object': ['/objects'],
        'zone': ['/zones','/zones/dungeons','/zones/raids'],
        'faction': ['/factions'],
    }.items():
        for p in paths:
            # Expansion-specific zones
            if exp == 'tbc' and typ == 'quest':
                pass
            FULL_TARGETS.append((exp, typ, p))
    if exp in ('tbc','wotlk'):
        FULL_TARGETS.append((exp,'quest','/quests/outland'))
    if exp == 'wotlk':
        FULL_TARGETS.append((exp,'quest','/quests/northrend'))
        FULL_TARGETS.append((exp,'title','/titles'))
        FULL_TARGETS.append((exp,'achievement','/achievements'))
        FULL_TARGETS.append((exp,'currency','/currencies'))


def rows_from_browser(page, expansion, entity_type, url):
    page.goto(url, wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(3500)

    js_rows = page.evaluate("""() => {
        const out = [];
        function addArray(arr, source) {
            if (!Array.isArray(arr)) return;
            for (const x of arr) {
                if (x && typeof x === 'object' && x.id != null && (x.name || x.name_enus)) {
                    out.push({id: x.id, name: x.name || x.name_enus, source, raw: x});
                }
            }
        }
        for (const k of Object.keys(window)) {
            if (/^listview/i.test(k)) addArray(window[k], k);
        }
        if (window.g_listviews) {
            for (const key of Object.keys(window.g_listviews)) {
                const lv = window.g_listviews[key];
                if (lv && Array.isArray(lv.data)) addArray(lv.data, 'g_listviews.' + key);
            }
        }
        // DOM fallback for rendered anchors
        document.querySelectorAll(`a[href*="/${'$'}{''}"]`).forEach(a => {});
        return out;
    }""")

    # Python/DOM fallback from all anchors.
    html = page.content()
    link_re = re.compile(rf'href="([^"]*/{re.escape(entity_type)}=(\d+)[^"]*)"[^>]*>(.*?)</a>', re.I|re.S)
    dom_rows = []
    for href, idstr, inner in link_re.findall(html):
        name = re.sub('<.*?>', '', inner)
        name = re.sub(r'\s+', ' ', name).strip()
        if name:
            dom_rows.append({'id': int(idstr), 'name': name, 'source': 'dom-link', 'raw': {}})

    by_id = {}
    for x in list(js_rows or []) + dom_rows:
        try:
            eid = int(x.get('id'))
        except Exception:
            continue
        name = str(x.get('name') or '').strip()
        if not name:
            continue
        by_id[eid] = {
            'expansion': expansion,
            'type': entity_type,
            'id': eid,
            'name': name,
            'url': f"{URL_PREFIX[expansion]}/{entity_type}={eid}",
            'source': 'wowhead-listview',
            'meta': {'listview_source': x.get('source'), 'page': url},
        }
    return list(by_id.values()), html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sample', action='store_true')
    ap.add_argument('--headed', action='store_true')
    ap.add_argument('--debug', action='store_true')
    args = ap.parse_args()

    targets = SAMPLE_TARGETS if args.sample else FULL_TARGETS
    debug_dir = Path(__file__).resolve().parents[1] / 'data' / 'exports' / 'debug'
    debug_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        page = browser.new_page(viewport={'width': 1400, 'height': 1000})
        for expansion, entity_type, path in targets:
            url = urljoin(URL_PREFIX[expansion] + '/', path.lstrip('/'))
            print(f"Fetching {expansion} {entity_type}: {url}")
            try:
                rows, html = rows_from_browser(page, expansion, entity_type, url)
                write_exports(expansion, entity_type, rows)
                total += len(rows)
                print(f"  -> {len(rows)} rows")
                if args.debug:
                    safe = f"{expansion}_{entity_type}_{path.strip('/').replace('/','_') or 'root'}"
                    (debug_dir / f"{safe}.html").write_text(html, encoding='utf-8')
                    page.screenshot(path=str(debug_dir / f"{safe}.png"), full_page=True)
            except Exception as e:
                print(f"  !! failed: {e}")
        browser.close()
    print(f"\nDone. Total rows from this run: {total}")

if __name__ == '__main__':
    main()
