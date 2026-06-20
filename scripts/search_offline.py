from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.db import connect
from src.mangos import commands_for

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expansion", default="all", choices=["all", "vanilla", "classic", "tbc", "wotlk"])
    parser.add_argument("--type", default="all", choices=["all", "item", "quest", "npc", "object"])
    parser.add_argument("--sort", default="id_asc", choices=["id_asc", "id_desc", "name_asc", "name_desc"])
    parser.add_argument("query", nargs="?", default="")
    args = parser.parse_args()

    expansion = "vanilla" if args.expansion == "classic" else args.expansion
    order = {"id_asc":"e.id ASC","id_desc":"e.id DESC","name_asc":"e.name ASC","name_desc":"e.name DESC"}[args.sort]
    conn = connect()
    params = []

    if args.query:
        from_clause = "entries_fts f JOIN entries e ON e.rowid = f.rowid"
        where = ["entries_fts MATCH ?"]
        params.append(args.query)
    else:
        from_clause = "entries e"
        where = []

    if expansion != "all":
        where.append("e.expansion = ?"); params.append(expansion)
    if args.type != "all":
        where.append("e.type = ?"); params.append(args.type)

    sql = f"SELECT e.* FROM {from_clause}"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += f" ORDER BY {order} LIMIT 50"

    rows = conn.execute(sql, params).fetchall()
    if not rows:
        print("No results.")
        return

    for row in rows:
        d = dict(row)
        print(f"[{d['expansion']}] {d['type']} {d['id']} - {d['name']}")
        print(f"  {d['url']}")
        for cmd in commands_for(d):
            print(f"    {cmd}")

if __name__ == "__main__":
    main()
