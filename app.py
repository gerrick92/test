from __future__ import annotations
import json
from flask import Flask, render_template, request
from src.db import connect
from src.mangos import commands_for
app=Flask(__name__)
EXP=[("all","All expansions"),("vanilla","Vanilla"),("tbc","TBC"),("wotlk","WotLK")]
TYPES=[("all","All types"),("quest","Quests"),("item","Items"),("npc","NPCs"),("object","Objects")]
SORTS=[("id_asc","ID low → high"),("id_desc","ID high → low"),("name_asc","Name A → Z"),("name_desc","Name Z → A")]
@app.route("/")
def index():
    q=request.args.get("q","").strip(); exp=request.args.get("expansion","all"); typ=request.args.get("type","all"); sort=request.args.get("sort","id_asc")
    order={"id_asc":"e.id ASC","id_desc":"e.id DESC","name_asc":"e.name ASC","name_desc":"e.name DESC"}.get(sort,"e.id ASC")
    rows=[]; total=0; counts=[]; error=None
    try:
        conn=connect(); total=conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        counts=conn.execute("SELECT expansion,type,COUNT(*) c FROM entries GROUP BY expansion,type ORDER BY expansion,type").fetchall()
        params=[]
        if q:
            frm="entries_fts f JOIN entries e ON e.rowid=f.rowid"; where=["entries_fts MATCH ?"]; params.append(q)
        else:
            frm="entries e"; where=[]
        if exp!="all": where.append("e.expansion=?"); params.append(exp)
        if typ!="all": where.append("e.type=?"); params.append(typ)
        sql=f"SELECT e.* FROM {frm}" + ((" WHERE "+" AND ".join(where)) if where else "") + f" ORDER BY {order} LIMIT 200"
        for r in conn.execute(sql,params):
            d=dict(r)
            try: d["meta_obj"]=json.loads(d.get("meta") or "{}")
            except Exception: d["meta_obj"]={}
            d["commands"]=commands_for(d); rows.append(d)
    except Exception as exc: error=str(exc)
    return render_template("index.html", q=q, expansion=exp, typ=typ, sort=sort, expansions=EXP, types=TYPES, sorts=SORTS, rows=rows, total=total, counts=counts, error=error)
if __name__=="__main__": app.run(debug=True)
