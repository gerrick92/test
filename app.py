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

ITEM_GROUPS = [
    ("all", "All item groups"),
    ("cloth", "Cloth"),
    ("leather", "Leather"),
    ("mail", "Mail"),
    ("plate", "Plate"),
    ("weapons", "Weapons"),
    ("jewelry", "Jewelry"),
    ("trinkets", "Trinkets"),
    ("consumables", "Consumables"),
    ("quest", "Quest items"),
    ("misc", "Misc"),
]

EQUIP_SLOTS = [
    ("all", "All slots"),
    ("head", "Head"),
    ("chest", "Chest"),
    ("legs", "Legs"),
    ("feet", "Feet"),
    ("hands", "Hands"),
    ("ring", "Ring"),
    ("trinket", "Trinket"),
    ("weapon", "Weapon"),
]

# Vanilla/TBC/WotLK item_template class values
# 0 Consumable, 2 Weapon, 4 Armor, 12 Quest, 15 Misc
# Armor subclass: 1 Cloth, 2 Leather, 3 Mail, 4 Plate
# InventoryType: 1 Head, 5 Chest, 7 Legs, 8 Feet, 10 Hands, 11 Finger, 12 Trinket, 13-17/Ranged etc Weapon-ish
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

def pagination_window(page: int, max_page: int, width: int = 9) -> list[int]:
    if max_page <= width:
        return list(range(1, max_page + 1))

    half = width // 2
    start = max(1, page - half)
    end = min(max_page, start + width - 1)
    start = max(1, end - width + 1)
    return list(range(start, end + 1))

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    expansion = request.args.get("expansion", "all")
    typ = request.args.get("type", "all")
    sort = request.args.get("sort", "id_asc")
    item_group = request.args.get("item_group", "all")
    equip_slot = request.args.get("equip_slot", "all")
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

        if item_group != "all":
            where.append("e.type = 'item'")
            where.append(ITEM_GROUP_SQL.get(item_group, "1=1"))

        if equip_slot != "all":
            where.append("e.type = 'item'")
            where.append(EQUIP_SLOT_SQL.get(equip_slot, "1=1"))

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

    pages = pagination_window(page, max_page)

    def page_url(target_page: int) -> str:
        return url_for(
            "index",
            q=q,
            expansion=expansion,
            type=typ,
            sort=sort,
            item_group=item_group,
            equip_slot=equip_slot,
            page=target_page,
            per_page=per_page,
        )

    return render_template(
        "index.html",
        q=q,
        expansion=expansion,
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
        expansions=EXPANSIONS,
        types=TYPES,
        sorts=SORTS,
        item_groups=ITEM_GROUPS,
        equip_slots=EQUIP_SLOTS,
        rows=rows,
        total=total,
        match_total=match_total,
        counts=counts,
        error=error,
    )

if __name__ == "__main__":
    app.run(debug=True)
