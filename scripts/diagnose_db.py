from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.db import connect, integrity
conn=connect()
print("SQLite integrity_check:", integrity(conn))
print("\nCounts by expansion/type")
for r in conn.execute("SELECT expansion,type,COUNT(*) c FROM entries GROUP BY expansion,type ORDER BY expansion,type"):
    print(f"{r['expansion']:8} {r['type']:8} {r['c']:8}")
print("\nTotal entries:", conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0])
print("\nSample")
for r in conn.execute("SELECT expansion,type,id,name,source_table FROM entries ORDER BY expansion,type,id LIMIT 40"):
    print(f"{r['expansion']:8} {r['type']:8} {r['id']:8} {r['name']} ({r['source_table']})")
print("\nWarnings/zero imports")
for r in conn.execute("SELECT expansion,source_file,table_name,imported_type,imported_count,note FROM import_log WHERE imported_count=0 OR note!='' ORDER BY id DESC LIMIT 100"):
    print(f"[{r['expansion']}] {r['source_file']} table={r['table_name']} type={r['imported_type']} count={r['imported_count']} note={r['note']}")
