
from __future__ import annotations

import json
from flask import Flask, render_template, request, url_for, redirect

from src.db import connect
from src.mangos import commands_for

app = Flask(__name__)

EXPANSION_DATA = {
    "vanilla": {"label": "Vanilla", "title": "World of Warcraft Classic", "logo": "vanilla_logo_large.webp", "icon": "vanilla_icon.jpg", "body_class": "page-vanilla"},
    "tbc": {"label": "TBC", "title": "The Burning Crusade", "logo": "tbc_logo_large.jpg", "icon": "tbc_icon.jpg", "body_class": "page-tbc"},
    "wotlk": {"label": "WotLK", "title": "Wrath of the Lich King", "logo": "wotlk_logo_large.jpg", "icon": "wotlk_icon.png", "body_class": "page-wotlk"},
    "all": {"label": "All Data", "title": "All Expansions", "logo": None, "icon": "home_hearthstone.webp", "body_class": "page-all"},
}

TYPES = [("quest", "Quests"), ("item", "Items"), ("npc", "NPCs"), ("object", "Objects")]
TYPE_ALL = [("all", "All types"), *TYPES]
SORTS = [("id_asc", "ID low → high"), ("id_desc", "ID high → low"), ("name_asc", "Name A → Z"), ("name_desc", "Name Z → A")]
PER_PAGE_OPTIONS = [50, 100, 200, 500]

ITEM_GROUPS = [
    ("all", "All item groups"), ("cloth", "Cloth"), ("leather", "Leather"), ("mail", "Mail"),
    ("plate", "Plate"), ("weapons", "Weapons"), ("jewelry", "Jewelry"), ("trinkets", "Trinkets"),
    ("consumables", "Consumables"), ("quest", "Quest items"), ("misc", "Misc"),
]
EQUIP_SLOTS = [
    ("all", "All slots"), ("head", "Head"), ("chest", "Chest"), ("legs", "Legs"),
    ("feet", "Feet"), ("hands", "Hands"), ("ring", "Ring"), ("trinket", "Trinket"), ("weapon", "Weapon"),
]

ITEM_GROUP_SQL = {
    "cloth": "json_extract(e.meta, '$.class') = '4' AND json_extract(e.meta, '$.subclass') = '1'",
    "leather": "json_extract(e.meta, '$.class') = '4' AND json_extract(e.meta, '$.subclass') = '2'",
    "mail": "json_extract(e.meta, '$.class') = '4' AND json_extract(e.meta, '$.subclass') = '3'",
    "plate": "json_extract(e.meta, '$.class') = '4' AND json_extract(e.meta, '$.subclass') = '4'",
    "weapons": "json_extract(e.meta, '$.class') = '2'",
    "jewelry": "json_extract(e.meta, '$.InventoryType') IN ('2','11','12','23')",
    "trinkets": "json_extract(e.meta, '$.InventoryType') = '12'",
    "consumables": "json_extract(e.meta, '$.class') = '0'",
    "quest": "json_extract(e.meta, '$.class') = '12'",
    "misc": "json_extract(e.meta, '$.class') = '15'",
}
EQUIP_SLOT_SQL = {
    "head": "json_extract(e.meta, '$.InventoryType') = '1'",
    "chest": "json_extract(e.meta, '$.InventoryType') IN ('5','20')",
    "legs": "json_extract(e.meta, '$.InventoryType') = '7'",
    "feet": "json_extract(e.meta, '$.InventoryType') = '8'",
    "hands": "json_extract(e.meta, '$.InventoryType') = '10'",
    "ring": "json_extract(e.meta, '$.InventoryType') = '11'",
    "trinket": "json_extract(e.meta, '$.InventoryType') = '12'",
    "weapon": "json_extract(e.meta, '$.InventoryType') IN ('13','14','15','16','17','21','22','25','26','28')",
}

def safe_int(value: str | None, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value or default)
    except ValueError:
        return default
    return max(minimum, min(maximum, parsed))

def pagination_window(page: int, max_page: int, width: int = 5) -> list[int]:
    if max_page <= width:
        return list(range(1, max_page + 1))
    half = width // 2
    start = max(1, page - half)
    end = min(max_page, start + width - 1)
    start = max(1, end - width + 1)
    return list(range(start, end + 1))

@app.route("/")
def home():
    total = 0
    counts = []
    try:
        conn = connect()
        total = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        counts = conn.execute("SELECT expansion, type, COUNT(*) c FROM entries GROUP BY expansion, type ORDER BY expansion, type").fetchall()
    except Exception:
        pass
    return render_template("home.html", expansion_data=EXPANSION_DATA, total=total, counts=counts)

@app.route("/settings")
def settings():
    total = 0
    counts = []
    error = None
    try:
        conn = connect()
        total = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        counts = conn.execute("SELECT expansion, type, COUNT(*) c FROM entries GROUP BY expansion, type ORDER BY expansion, type").fetchall()
    except Exception as exc:
        error = str(exc)
    return render_template("settings.html", total=total, counts=counts, error=error, body_class="page-settings")

@app.route("/expansion/<expansion>")
def expansion_page(expansion: str):
    if expansion not in EXPANSION_DATA:
        return redirect(url_for("home"))

    q = request.args.get("q", "").strip()
    typ = request.args.get("type", "quest")
    sort = request.args.get("sort", "id_asc")
    item_group = request.args.get("item_group", "all")
    equip_slot = request.args.get("equip_slot", "all")
    page = safe_int(request.args.get("page"), 1, 1, 999999)
    per_page = safe_int(request.args.get("per_page"), 200, 50, 500)

    if typ != "item":
        item_group = "all"
        equip_slot = "all"

    order = {"id_asc": "e.id ASC", "id_desc": "e.id DESC", "name_asc": "e.name ASC", "name_desc": "e.name DESC"}.get(sort, "e.id ASC")

    rows = []
    total = 0
    match_total = 0
    error = None

    try:
        conn = connect()
        total = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]

        where = []
        params = []

        if expansion != "all":
            where.append("e.expansion = ?")
            params.append(expansion)

        if typ != "all":
            where.append("e.type = ?")
            params.append(typ)

        if typ == "item":
            if item_group != "all":
                where.append(ITEM_GROUP_SQL.get(item_group, "1=1"))
            if equip_slot != "all":
                where.append(EQUIP_SLOT_SQL.get(equip_slot, "1=1"))

        if q:
            if q.isdigit():
                where.append("(e.id = ? OR e.name LIKE ?)")
                params.extend([int(q), f"%{q}%"])
            else:
                where.append("e.name LIKE ?")
                params.append(f"%{q}%")

        where_sql = " WHERE " + " AND ".join(where) if where else ""
        match_total = conn.execute(f"SELECT COUNT(*) FROM entries e{where_sql}", params).fetchone()[0]
        max_page = max(1, (match_total + per_page - 1) // per_page)
        page = min(page, max_page)
        offset = (page - 1) * per_page

        sql = f"SELECT e.* FROM entries e {where_sql} ORDER BY {order} LIMIT ? OFFSET ?"
        for r in conn.execute(sql, [*params, per_page, offset]):
            d = dict(r)
            try:
                d["meta_obj"] = json.loads(d.get("meta") or "{}")
            except Exception:
                d["meta_obj"] = {}
            d["commands"] = commands_for(d)
            rows.append(d)

    except Exception as exc:
        error = str(exc)
        max_page = 1

    pages = pagination_window(page, max_page)

    def page_url(target_page: int) -> str:
        return url_for("expansion_page", expansion=expansion, q=q, type=typ, sort=sort, item_group=item_group, equip_slot=equip_slot, page=target_page, per_page=per_page)

    return render_template(
        "expansion.html",
        expansion=expansion,
        current=EXPANSION_DATA[expansion],
        q=q,
        typ=typ,
        sort=sort,
        item_group=item_group,
        equip_slot=equip_slot,
        page=page,
        per_page=per_page,
        per_page_options=PER_PAGE_OPTIONS,
        max_page=max_page,
        pages=pages,
        page_url=page_url,
        types=TYPE_ALL if expansion == "all" else TYPES,
        sorts=SORTS,
        item_groups=ITEM_GROUPS,
        equip_slots=EQUIP_SLOTS,
        rows=rows,
        total=total,
        match_total=match_total,
        error=error,
        body_class=EXPANSION_DATA[expansion]["body_class"],
    )

if __name__ == "__main__":
    app.run(debug=True)
