from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    expansion TEXT NOT NULL,
    type TEXT NOT NULL,
    id INTEGER NOT NULL,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    source TEXT,
    meta TEXT,
    PRIMARY KEY (expansion, type, id)
);
"""

def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()

def rebuild_fts(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS entries_fts")
    conn.execute("""
        CREATE VIRTUAL TABLE entries_fts USING fts5(
            name,
            expansion,
            type
        )
    """)
    conn.execute("""
        INSERT INTO entries_fts(rowid, name, expansion, type)
        SELECT rowid, name, expansion, type FROM entries
    """)
    conn.commit()
