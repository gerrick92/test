from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import EXPORTS, DB_DIR
from src.db import connect, init_db, rebuild_fts

DB_PATH = DB_DIR / 'wow.db'


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = connect(DB_PATH)
    init_db(conn)
    total = 0
    for path in sorted(EXPORTS.glob('*.json')):
        if path.name.startswith('failures'):
            continue
        try:
            rows = json.loads(path.read_text(encoding='utf-8'))
        except Exception as e:
            print(f"Skipping {path.name}: {e}")
            continue
        count = 0
        for r in rows:
            try:
                conn.execute(
                    "INSERT OR REPLACE INTO entries(expansion,type,id,name,url,source,meta) VALUES(?,?,?,?,?,?,?)",
                    (r.get('expansion'), r.get('type'), int(r.get('id')), r.get('name'), r.get('url'), r.get('source'), json.dumps(r.get('meta',{}), ensure_ascii=False))
                )
                count += 1
            except Exception:
                pass
        conn.commit()
        total += count
        print(f"Imported {count:6d} rows from {path.name}")
    rebuild_fts(conn)
    integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
    print(f"SQLite integrity_check: {integrity}")
    print(f"Built database: {total} rows")
    print(f"DB: {DB_PATH}")

if __name__ == '__main__':
    main()
