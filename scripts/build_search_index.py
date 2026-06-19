from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db import connect, create_fts, integrity

conn = connect()
create_fts(conn)
print("SQLite integrity_check:", integrity(conn))
print("Rebuilt search index.")
