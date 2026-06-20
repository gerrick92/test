from __future__ import annotations

import json
from flask import Flask, render_template, request, url_for

from src.db import connect
from src.mangos import commands_for

app = Flask(__name__)

EXPANSIONS = [
    ("all", "All expansions"),
    ("vanilla", "Vanilla"),
    ("tbc", "TBC"),
    ("wotlk", "WotLK"),
]

TYPES = [
    ("all", "All types"),
    ("quest", "Quests"),
    ("item", "Items"),
    ("npc", "NPCs"),
    ("object", "Objects"),
]

SORTS = [
    ("id_asc", "ID low → high"),
    ("id_desc", "ID high → low"),
    ("name_asc", "Name A → Z"),
    ("name_desc", "Name Z → A"),
]

PER_PAGE_OPTIONS = [50, 100, 200, 500]

def safe_int(value: str | None, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value or default)
    except ValueError:
        return default
    return max(minimum, min(maximum, parsed))

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    expansion = request.args.get("expansion", "all")
    typ = request.args.get("type", "all")
    sort = request.args.get("sort", "id_asc")
    page = safe_int(request.args.get("page"), 1, 1, 999999)
    per_page = safe_int(request.args.get("per_page"), 200, 50, 500)

    order = {
        "id_asc": "e.id ASC",
        "id_desc": "e.id DESC",
        "name_asc": "e.name ASC",
        "name_desc": "e.name DESC",
    }.get(sort, "e.id ASC")

    conn = connect()
    rows = []
    total = 0
    match_total = 0
    counts = []
    error = None

    try:
        total = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        counts = conn.execute(
            "SELECT expansion, type, COUNT(*) c FROM entries GROUP BY expansion, type ORDER BY expansion, type"
        ).fetchall()

        where = []
        params: list[object] = []

        if expansion != "all":
            where.append("e.expansion = ?")
            params.append(expansion)
        if typ != "all":
            where.append("e.type = ?")
            params.append(typ)

        # Better search:
        # - numeric query searches exact ID OR name
        # - text query searches LIKE. This is slower than FTS but more forgiving for WoW names.
        if q:
            if q.isdigit():
                where.append("(e.id = ? OR e.name LIKE ?)")
                params.extend([int(q), f"%{q}%"])
            else:
                where.append("e.name LIKE ?")
                params.append(f"%{q}%")

        where_sql = " WHERE " + " AND ".join(where) if where else ""

        count_sql = f"SELECT COUNT(*) FROM entries e{where_sql}"
        match_total = conn.execute(count_sql, params).fetchone()[0]

        max_page = max(1, (match_total + per_page - 1) // per_page)
        if page > max_page:
            page = max_page

        offset = (page - 1) * per_page

        sql = f"""
            SELECT e.*
            FROM entries e
            {where_sql}
            ORDER BY {order}
            LIMIT ? OFFSET ?
        """
        query_params = [*params, per_page, offset]

        for r in conn.execute(sql, query_params):
            d = dict(r)
            try:
                d["meta_obj"] = json.loads(d.get("meta") or "{}")
            except Exception:
                d["meta_obj"] = {}
            d["commands"] = commands_for(d)
            rows.append(d)

    except Exception as exc:
        error = str(exc)
        match_total = 0
        max_page = 1

    def page_url(target_page: int) -> str:
        return url_for(
            "index",
            q=q,
            expansion=expansion,
            type=typ,
            sort=sort,
            page=target_page,
            per_page=per_page,
        )

    return render_template(
        "index.html",
        q=q,
        expansion=expansion,
        typ=typ,
        sort=sort,
        page=page,
        per_page=per_page,
        per_page_options=PER_PAGE_OPTIONS,
        max_page=max_page,
        page_url=page_url,
        expansions=EXPANSIONS,
        types=TYPES,
        sorts=SORTS,
        rows=rows,
        total=total,
        match_total=match_total,
        counts=counts,
        error=error,
    )

if __name__ == "__main__":
    app.run(debug=True)
