from __future__ import annotations

import argparse, csv, gzip, io, json, re, sqlite3, sys, zipfile
from pathlib import Path
from typing import Iterable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.db import connect, reset_schema, create_fts, integrity, DB_PATH

INPUT_ROOT = Path("data/input")
EXPANSION_URL = {"vanilla":"classic","classic":"classic","tbc":"tbc","wotlk":"wotlk"}

TABLE_MAP = {
    "item_template": {"type":"item","id_cols":["entry","id"],"name_cols":["name","Name"],"meta_cols":["class","subclass","Quality","ItemLevel","RequiredLevel","InventoryType","SellPrice"]},
    "quest_template": {"type":"quest","id_cols":["entry","id","QuestID","quest_id"],"name_cols":["Title","title","name","Name","LogTitle"],"meta_cols":["MinLevel","MaxLevel","QuestLevel","ZoneOrSort","Type","PrevQuestId","NextQuestId","NextQuestInChain"]},
    "creature_template": {"type":"npc","id_cols":["entry","Entry","id"],"name_cols":["Name","name"],"meta_cols":["SubName","MinLevel","MaxLevel","Faction","CreatureType","Rank","NpcFlags"]},
    "gameobject_template": {"type":"object","id_cols":["entry","Entry","id"],"name_cols":["name","Name"],"meta_cols":["type","displayId","faction","flags"]},
}

CREATE_RE = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?(?P<table>[A-Za-z0-9_]+)`?\s*\((?P<body>.*?)\)\s*[^;]*;", re.I|re.S)
INSERT_START_RE = re.compile(r"INSERT\s+(?:IGNORE\s+)?INTO\s+`?(?P<table>[A-Za-z0-9_]+)`?\s*(?:\((?P<cols>.*?)\))?\s*VALUES\s*", re.I|re.S)

def iter_input_files(path: Path, include_updates: bool) -> Iterable[Path]:
    if path.is_file():
        yield path; return
    if not path.exists(): return
    files = [p for p in path.rglob("*") if p.is_file() and (p.name.lower().endswith(".sql") or p.name.lower().endswith(".sql.gz") or p.name.lower().endswith(".zip"))]
    if not include_updates:
        full_db = [p for p in files if "full_db" in str(p).lower()]
        if full_db:
            yield from sorted(full_db); return
        zips = [p for p in files if p.name.lower().endswith(".zip")]
        if zips:
            yield from sorted(zips); return
    yield from sorted(files)

def iter_sql_texts_from_file(path: Path, include_updates: bool) -> Iterable[tuple[str, str]]:
    lower = path.name.lower()
    if lower.endswith(".zip"):
        with zipfile.ZipFile(path, "r") as z:
            names = z.namelist()
            if not include_updates:
                full_names = [n for n in names if "full_db/" in n.lower() and (n.lower().endswith(".sql") or n.lower().endswith(".sql.gz"))]
                if full_names: names = full_names
            for name in names:
                nl = name.lower()
                if not (nl.endswith(".sql") or nl.endswith(".sql.gz")): continue
                with z.open(name) as f:
                    raw = f.read()
                    if nl.endswith(".gz"): raw = gzip.decompress(raw)
                    yield name, raw.decode("utf-8", errors="replace")
    elif lower.endswith(".sql.gz"):
        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f: yield path.name, f.read()
    elif lower.endswith(".sql"):
        yield path.name, path.read_text(encoding="utf-8", errors="replace")

def split_sql_columns(body: str) -> list[str]:
    cols = []
    for line in body.splitlines():
        line = line.strip().rstrip(",")
        if line.startswith("`"):
            m = re.match(r"`([^`]+)`", line)
            if m: cols.append(m.group(1))
    return cols

def parse_create_tables(text: str) -> dict[str, list[str]]:
    out = {}
    for m in CREATE_RE.finditer(text):
        table = m.group("table")
        if table in TABLE_MAP:
            cols = split_sql_columns(m.group("body"))
            if cols: out[table] = cols
    return out

def find_statement_end(text: str, start: int) -> int:
    in_str = False; esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc: esc = False
            elif ch == "\\": esc = True
            elif ch == "'": in_str = False
        else:
            if ch == "'": in_str = True
            elif ch == ";": return i
    return len(text)

def iter_insert_statements(text: str) -> Iterable[tuple[str, str | None, str]]:
    pos = 0
    while True:
        m = INSERT_START_RE.search(text, pos)
        if not m: break
        end = find_statement_end(text, m.end())
        yield m.group("table"), m.group("cols"), text[m.end():end]
        pos = end + 1

def parse_insert_cols(cols: str | None) -> list[str] | None:
    if not cols: return None
    return [c.strip().strip("`") for c in cols.split(",")]

def split_values(values: str) -> list[str]:
    rows=[]; buf=[]; depth=0; in_str=False; esc=False
    for ch in values:
        if in_str:
            buf.append(ch)
            if esc: esc=False
            elif ch=="\\": esc=True
            elif ch=="'": in_str=False
            continue
        if ch=="'":
            in_str=True; buf.append(ch)
        elif ch=="(":
            depth+=1
            if depth==1: buf=[]
            else: buf.append(ch)
        elif ch==")":
            depth-=1
            if depth==0:
                rows.append("".join(buf)); buf=[]
            else: buf.append(ch)
        else:
            if depth>=1: buf.append(ch)
    return rows

def parse_row(row: str) -> list[str | None]:
    reader = csv.reader(io.StringIO(row), delimiter=",", quotechar="'", escapechar="\\", doublequote=False, skipinitialspace=True)
    raw = next(reader)
    return [None if v.strip().upper()=="NULL" else v.strip() for v in raw]

def find_col(cols: list[str], candidates: list[str]) -> int | None:
    lower=[c.lower() for c in cols]
    for cand in candidates:
        if cand.lower() in lower: return lower.index(cand.lower())
    return None

def wowhead_url(expansion: str, typ: str, eid: int) -> str:
    prefix=EXPANSION_URL.get(expansion, expansion)
    wow_type="npc" if typ=="npc" else typ
    return f"https://www.wowhead.com/{prefix}/{wow_type}={eid}"

def log_import(conn, expansion, source_file, table, typ, count, note=""):
    conn.execute("INSERT INTO import_log(expansion, source_file, table_name, imported_type, imported_count, note) VALUES (?, ?, ?, ?, ?, ?)", (expansion, source_file, table, typ, count, note))

def import_sql_text(conn: sqlite3.Connection, expansion: str, label: str, text: str) -> dict[str, int]:
    create_cols = parse_create_tables(text)
    counts = {}
    for table, raw_cols, raw_values in iter_insert_statements(text):
        if table not in TABLE_MAP: continue
        info=TABLE_MAP[table]; typ=info["type"]
        cols = parse_insert_cols(raw_cols) or create_cols.get(table)
        if not cols:
            log_import(conn, expansion, label, table, typ, 0, "Skipped: no columns found"); continue
        id_idx=find_col(cols, info["id_cols"]); name_idx=find_col(cols, info["name_cols"])
        if id_idx is None or name_idx is None:
            log_import(conn, expansion, label, table, typ, 0, f"Skipped: no id/name column in first columns {cols[:40]}"); continue

        meta_indices=[]
        for mcol in info.get("meta_cols", []):
            idx=find_col(cols, [mcol])
            if idx is not None: meta_indices.append((mcol, idx))

        imported=0
        for row_text in split_values(raw_values):
            try:
                row=parse_row(row_text)
                if id_idx>=len(row) or name_idx>=len(row): continue
                eid_raw=row[id_idx]; name_raw=row[name_idx]
                if eid_raw is None or name_raw is None: continue
                eid=int(str(eid_raw)); name=str(name_raw).strip()
                if not name: continue
                meta={"source_file": label, "source_table": table}
                for mcol, idx in meta_indices:
                    if idx < len(row) and row[idx] not in (None, ""):
                        meta[mcol]=row[idx]
                conn.execute("""INSERT OR REPLACE INTO entries
                    (expansion, type, id, name, url, source_table, meta)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (expansion, typ, eid, name, wowhead_url(expansion, typ, eid), table, json.dumps(meta, ensure_ascii=False)))
                imported += 1
            except Exception:
                continue
        if imported: counts[typ]=counts.get(typ,0)+imported
        log_import(conn, expansion, label, table, typ, imported)
    conn.commit()
    return counts

def import_expansion(conn, expansion: str, path: Path, include_updates: bool):
    print(f"\n=== Importing {expansion}: {path} ===")
    total={}
    files=list(iter_input_files(path, include_updates))
    if not files:
        print(f"No input files found for {expansion}: {path}")
        log_import(conn, expansion, str(path), None, None, 0, "No input files found"); return
    for file in files:
        print(f"Reading {file}")
        for label, text in iter_sql_texts_from_file(file, include_updates):
            counts=import_sql_text(conn, expansion, label, text)
            if counts: print(f"  {label}: {counts}")
            for k,v in counts.items(): total[k]=total.get(k,0)+v
    print(f"TOTAL {expansion}: {total}")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--expansion", choices=["vanilla","classic","tbc","wotlk"])
    parser.add_argument("--path")
    parser.add_argument("--append", action="store_true")
    parser.add_argument("--include-updates", action="store_true")
    args=parser.parse_args()

    conn=connect(DB_PATH)
    if not args.append: reset_schema(conn)

    if args.all:
        import_expansion(conn, "vanilla", INPUT_ROOT/"vanilla", args.include_updates)
        import_expansion(conn, "tbc", INPUT_ROOT/"tbc", args.include_updates)
        import_expansion(conn, "wotlk", INPUT_ROOT/"wotlk", args.include_updates)
    else:
        if not args.expansion: raise SystemExit("Use --all or --expansion")
        expansion="vanilla" if args.expansion=="classic" else args.expansion
        path=Path(args.path) if args.path else INPUT_ROOT/expansion
        import_expansion(conn, expansion, path, args.include_updates)

    create_fts(conn)
    print("SQLite integrity_check:", integrity(conn))
    total=conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
    print(f"Built DB with {total} entries: {DB_PATH}")
    print("Run: python scripts\\diagnose_db.py")

if __name__=="__main__":
    main()
