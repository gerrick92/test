from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.db import connect
from src.mangos import commands_for

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--expansion", default="all", choices=["all","vanilla","classic","tbc","wotlk"])
    ap.add_argument("--type", default="all", choices=["all","item","quest","npc","object"])
    ap.add_argument("--sort", default="id_asc", choices=["id_asc","id_desc","name_asc","name_desc"])
    ap.add_argument("query", nargs="?", default="")
    a=ap.parse_args()
    exp="vanilla" if a.expansion=="classic" else a.expansion
    order={"id_asc":"e.id ASC","id_desc":"e.id DESC","name_asc":"e.name ASC","name_desc":"e.name DESC"}[a.sort]
    conn=connect(); params=[]
    if a.query:
        frm="entries_fts f JOIN entries e ON e.rowid=f.rowid"; where=["entries_fts MATCH ?"]; params.append(a.query)
    else:
        frm="entries e"; where=[]
    if exp!="all": where.append("e.expansion=?"); params.append(exp)
    if a.type!="all": where.append("e.type=?"); params.append(a.type)
    sql=f"SELECT e.* FROM {frm}" + ((" WHERE "+" AND ".join(where)) if where else "") + f" ORDER BY {order} LIMIT 50"
    rows=conn.execute(sql,params).fetchall()
    if not rows: print("No results."); return
    for r in rows:
        d=dict(r); print(f"[{d['expansion']}] {d['type']} {d['id']} - {d['name']}\n  {d['url']}")
        for cmd in commands_for(d): print("   ",cmd)
if __name__=="__main__": main()
