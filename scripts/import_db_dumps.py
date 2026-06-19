from __future__ import annotations
import argparse, csv, gzip, io, json, re, sqlite3, sys, zipfile
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.db import connect, reset_schema, create_fts, integrity, DB_PATH

INPUT_ROOT = Path("data/input")
EXPANSION_URL = {"vanilla":"classic","classic":"classic","tbc":"tbc","wotlk":"wotlk"}
TABLE_MAP = {
    "item_template": {"type":"item", "id_cols":["entry","id"], "name_cols":["name","Name"]},
    "quest_template": {"type":"quest", "id_cols":["entry","id","QuestID","quest_id"], "name_cols":["Title","title","name","Name","LogTitle"]},
    "creature_template": {"type":"npc", "id_cols":["entry","id"], "name_cols":["Name","name"]},
    "gameobject_template": {"type":"object", "id_cols":["entry","id"], "name_cols":["name","Name"]},
}
CREATE_RE = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?(?P<table>[A-Za-z0-9_]+)`?\s*\((?P<body>.*?)\)\s*[^;]*;", re.I|re.S)
INSERT_RE = re.compile(r"INSERT\s+(?:IGNORE\s+)?INTO\s+`?(?P<table>[A-Za-z0-9_]+)`?\s*(?:\((?P<cols>.*?)\))?\s*VALUES\s*(?P<values>.*?);", re.I|re.S)

def iter_input_files(path: Path):
    if path.is_file():
        yield path; return
    if not path.exists(): return
    for p in path.rglob("*"):
        l=p.name.lower()
        if p.is_file() and (l.endswith(".sql") or l.endswith(".sql.gz") or l.endswith(".zip")):
            yield p

def iter_sql_texts(path: Path):
    l=path.name.lower()
    if l.endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                nl=n.lower()
                if nl.endswith(".sql"):
                    yield n, z.open(n).read().decode("utf-8", errors="replace")
                elif nl.endswith(".sql.gz"):
                    with z.open(n) as f:
                        yield n, gzip.GzipFile(fileobj=f).read().decode("utf-8", errors="replace")
    elif l.endswith(".sql.gz"):
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
            yield path.name, f.read()
    elif l.endswith(".sql"):
        yield path.name, path.read_text(encoding="utf-8", errors="replace")

def create_cols(text: str) -> dict[str,list[str]]:
    out={}
    for m in CREATE_RE.finditer(text):
        t=m.group("table")
        if t not in TABLE_MAP: continue
        cols=[]
        for line in m.group("body").splitlines():
            line=line.strip().rstrip(",")
            if line.startswith("`"):
                mm=re.match(r"`([^`]+)`", line)
                if mm: cols.append(mm.group(1))
        if cols: out[t]=cols
    return out

def insert_cols(cols):
    if not cols: return None
    return [c.strip().strip("`") for c in cols.split(",")]

def split_values(values: str):
    rows=[]; buf=[]; depth=0; ins=False; esc=False
    for ch in values:
        if ins:
            buf.append(ch)
            if esc: esc=False
            elif ch=="\\": esc=True
            elif ch=="'": ins=False
        elif ch=="'":
            ins=True; buf.append(ch)
        elif ch=="(":
            depth+=1
            if depth==1: buf=[]
            else: buf.append(ch)
        elif ch==")":
            depth-=1
            if depth==0:
                rows.append("".join(buf)); buf=[]
            else: buf.append(ch)
        elif depth>=1:
            buf.append(ch)
    return rows

def parse_row(row: str):
    r=csv.reader(io.StringIO(row), delimiter=",", quotechar="'", escapechar="\\", doublequote=False, skipinitialspace=True)
    vals=next(r)
    return [None if v.strip().upper()=="NULL" else v.strip() for v in vals]

def find_col(cols, candidates):
    low=[c.lower() for c in cols]
    for cand in candidates:
        if cand.lower() in low: return low.index(cand.lower())
    return None

def wow_url(exp, typ, eid):
    p=EXPANSION_URL.get(exp, exp); wt="npc" if typ=="npc" else typ
    return f"https://www.wowhead.com/{p}/{wt}={eid}"

def log(conn, exp, file, table, typ, count, note=""):
    conn.execute("INSERT INTO import_log(expansion,source_file,table_name,imported_type,imported_count,note) VALUES (?,?,?,?,?,?)",(exp,file,table,typ,count,note))

def import_text(conn, exp, label, text):
    ccols=create_cols(text); totals={}
    for m in INSERT_RE.finditer(text):
        table=m.group("table")
        if table not in TABLE_MAP: continue
        info=TABLE_MAP[table]; typ=info["type"]
        cols=insert_cols(m.group("cols")) or ccols.get(table)
        if not cols:
            log(conn, exp, label, table, typ, 0, "no column order found"); continue
        iid=find_col(cols, info["id_cols"]); iname=find_col(cols, info["name_cols"])
        if iid is None or iname is None:
            log(conn, exp, label, table, typ, 0, "id/name columns not found"); continue
        n=0
        for rt in split_values(m.group("values")):
            try:
                row=parse_row(rt)
                if iid>=len(row) or iname>=len(row): continue
                eid_raw=row[iid]; name_raw=row[iname]
                if not eid_raw or not name_raw: continue
                eid=int(str(eid_raw)); name=str(name_raw).strip()
                if not name: continue
                meta={"source_file":label,"source_table":table}
                for k in ("subname","minlevel","maxlevel","level","RequiredLevel","QuestLevel","type","class","subclass"):
                    if k in cols:
                        idx=cols.index(k)
                        if idx < len(row): meta[k]=row[idx]
                conn.execute("""INSERT OR REPLACE INTO entries(expansion,type,id,name,url,source_table,meta) VALUES(?,?,?,?,?,?,?)""",
                    (exp,typ,eid,name,wow_url(exp,typ,eid),table,json.dumps(meta,ensure_ascii=False)))
                n+=1; totals[typ]=totals.get(typ,0)+1
            except Exception:
                continue
        log(conn, exp, label, table, typ, n)
    conn.commit(); return totals

def import_exp(conn, exp, path):
    print(f"\n=== {exp}: {path} ===")
    total={}
    files=list(iter_input_files(path))
    if not files:
        print("No files found"); log(conn,exp,str(path),None,None,0,"No files found"); return
    for f in files:
        print("Reading", f)
        for label,text in iter_sql_texts(f):
            counts=import_text(conn,exp,label,text)
            if counts: print(" ",label,counts)
            for k,v in counts.items(): total[k]=total.get(k,0)+v
    print("TOTAL", exp, total)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--expansion", choices=["vanilla","classic","tbc","wotlk"])
    ap.add_argument("--path")
    ap.add_argument("--append", action="store_true")
    args=ap.parse_args()
    conn=connect(DB_PATH)
    if not args.append: reset_schema(conn)
    if args.all:
        import_exp(conn,"vanilla",INPUT_ROOT/"vanilla")
        import_exp(conn,"tbc",INPUT_ROOT/"tbc")
        import_exp(conn,"wotlk",INPUT_ROOT/"wotlk")
    else:
        if not args.expansion: raise SystemExit("Use --all or --expansion")
        exp="vanilla" if args.expansion=="classic" else args.expansion
        import_exp(conn, exp, Path(args.path) if args.path else INPUT_ROOT/exp)
    create_fts(conn)
    print("SQLite integrity_check:", integrity(conn))
    print("Built DB with", conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0], "entries:", DB_PATH)
    print("Run: python scripts\\diagnose_db.py")
if __name__=="__main__": main()
