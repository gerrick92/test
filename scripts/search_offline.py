from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import DB_DIR

DB_PATH = DB_DIR / 'wow.db'

def mangos_commands(row):
    typ = row['type']; eid = row['id']; name = row['name']
    cmds = []
    if typ == 'item':
        cmds += [f".lookup item {name}", f".additem {eid} 1"]
    elif typ == 'quest':
        cmds += [f".lookup quest {name}", f".quest add {eid}", f".quest complete {eid}"]
    elif typ == 'npc':
        cmds += [f".lookup creature {name}", f".npc add {eid}", f".go creature {eid}"]
    elif typ == 'spell':
        cmds += [f".lookup spell {name}", f".learn {eid}", f".unlearn {eid}"]
    elif typ == 'object':
        cmds += [f".lookup object {name}", f".gobject add {eid}", f".go object {eid}"]
    return cmds

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('type', nargs='?', help='item, quest, npc, spell, etc. Use all for everything.')
    ap.add_argument('query', nargs='?', help='Name or ID')
    args = ap.parse_args()
    if not DB_PATH.exists():
        print('No results. Is data/db/wow.db built?')
        return
    if not args.query:
        print('Usage: python scripts\\search_offline.py quest "Diplomat"')
        return
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    typ = args.type or 'all'
    q = args.query.strip()
    params = []
    where_type = ''
    if typ != 'all':
        where_type = 'AND type = ?'
        params.append(typ)
    if q.isdigit():
        sql = f"SELECT * FROM entries WHERE id = ? {where_type} ORDER BY expansion,type,id LIMIT 50"
        rows = conn.execute(sql, [int(q)] + params).fetchall()
    else:
        like = f"%{q}%"
        sql = f"SELECT * FROM entries WHERE name LIKE ? {where_type} ORDER BY CASE WHEN name = ? THEN 0 WHEN name LIKE ? THEN 1 ELSE 2 END, expansion,type,id LIMIT 50"
        rows = conn.execute(sql, [like] + params + [q, q + '%']).fetchall()
    if not rows:
        print('No results.')
        return
    for r in rows:
        print(f"[{r['expansion']}] {r['type']} {r['id']} - {r['name']}")
        print(f"  {r['url']}")
        cmds = mangos_commands(r)
        if cmds:
            print('  MaNGOS:')
            for c in cmds:
                print(f"    {c}")

if __name__ == '__main__':
    main()
