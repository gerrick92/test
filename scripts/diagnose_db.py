from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.db import connect, integrity

conn = connect()
print("SQLite integrity_check:", integrity(conn))
print()
print("Counts by expansion/type")
print("------------------------")
for row in conn.execute("SELECT expansion, type, COUNT(*) c FROM entries GROUP BY expansion, type ORDER BY expansion, type"):
    print(f"{row['expansion']:8} {row['type']:8} {row['c']:8}")

print()
print("Total entries:", conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0])
print()
print("Quest ID sanity")
print("---------------")
for exp in ["vanilla", "tbc", "wotlk"]:
    rows = conn.execute(
        "SELECT id, name FROM entries WHERE expansion=? AND type='quest' ORDER BY id ASC LIMIT 20",
        (exp,),
    ).fetchall()
    print(exp)
    for r in rows:
        print(f"  {r['id']:6} {r['name']}")

print()
print("Warnings / skipped imports")
print("--------------------------")
for row in conn.execute("""
    SELECT expansion, source_file, table_name, imported_type, imported_count, note
    FROM import_log
    WHERE note != '' OR imported_count = 0
    ORDER BY id DESC
    LIMIT 80
"""):
    print(f"[{row['expansion']}] {row['source_file']} table={row['table_name']} type={row['imported_type']} count={row['imported_count']} note={row['note']}")
