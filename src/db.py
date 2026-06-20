from __future__ import annotations
import sqlite3
from pathlib import Path

DB_PATH = Path("data/db/wow.db")

SCHEMA = """
DROP TABLE IF EXISTS entries_fts;
DROP TABLE IF EXISTS entries;
DROP TABLE IF EXISTS import_log;

CREATE TABLE entries (
    expansion TEXT NOT NULL,
    type TEXT NOT NULL,
    id INTEGER NOT NULL,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    source_table TEXT NOT NULL,
    meta TEXT,
    PRIMARY KEY (expansion, type, id)
);

CREATE TABLE import_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expansion TEXT NOT NULL,
    source_file TEXT NOT NULL,
    table_name TEXT,
    imported_type TEXT,
    imported_count INTEGER NOT NULL,
    note TEXT
);
"""

def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def reset_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()

def create_fts(conn: sqlite3.Connection) -> None:
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

def integrity(conn: sqlite3.Connection) -> str:
    return conn.execute("PRAGMA integrity_check").fetchone()[0]
