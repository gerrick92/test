from __future__ import annotations
import sqlite3
from pathlib import Path
from flask import Flask, render_template, request

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / 'data' / 'db' / 'wow.db'
app = Flask(__name__)

def query_db(q='', typ='all', expansion='all'):
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    wheres=[]; params=[]
    if q:
        if q.isdigit():
            wheres.append('id = ?'); params.append(int(q))
        else:
            wheres.append('name LIKE ?'); params.append('%'+q+'%')
    if typ != 'all':
        wheres.append('type = ?'); params.append(typ)
    if expansion != 'all':
        wheres.append('expansion = ?'); params.append(expansion)
    where = 'WHERE ' + ' AND '.join(wheres) if wheres else ''
    return conn.execute(f'SELECT * FROM entries {where} ORDER BY expansion,type,id LIMIT 200', params).fetchall()

@app.route('/')
def index():
    q = request.args.get('q','').strip()
    typ = request.args.get('type','all')
    expansion = request.args.get('expansion','all')
    rows = query_db(q, typ, expansion) if q else []
    return render_template('index.html', rows=rows, q=q, typ=typ, expansion=expansion, db_exists=DB_PATH.exists())

if __name__ == '__main__':
    app.run(debug=True)
