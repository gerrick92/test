from __future__ import annotations
import sqlite3, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import DB_DIR
DB_PATH = DB_DIR / 'wow.db'
conn = sqlite3.connect(DB_PATH)
for row in conn.execute('SELECT expansion,type,COUNT(*) FROM entries GROUP BY expansion,type ORDER BY expansion,type'):
    print(f"{row[0]:8s} {row[1]:10s} {row[2]}")
print('integrity:', conn.execute('PRAGMA integrity_check').fetchone()[0])
