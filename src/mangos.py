from __future__ import annotations
def commands_for(entry: dict) -> list[str]:
    typ = entry.get("type")
    eid = entry.get("id")
    name = entry.get("name","")
    if typ == "item": return [f".lookup item {name}", f".additem {eid} 1"]
    if typ == "quest": return [f".lookup quest {name}", f".quest add {eid}", f".quest complete {eid}"]
    if typ == "npc": return [f".lookup creature {name}", f".npc add {eid}"]
    if typ == "object": return [f".lookup object {name}", f".gobject add {eid}"]
    return []
