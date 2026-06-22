from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EXPORTS = DATA / "exports"
CACHE = DATA / "cache"
DB_DIR = DATA / "db"

for p in (EXPORTS, CACHE, DB_DIR):
    p.mkdir(parents=True, exist_ok=True)

ENTITY_TYPES = {"item", "quest", "npc", "spell", "object", "zone", "faction", "achievement", "title", "currency"}
EXPANSIONS = {"classic", "tbc", "wotlk"}

URL_PREFIX = {
    "classic": "https://www.wowhead.com/classic",
    "tbc": "https://www.wowhead.com/tbc",
    "wotlk": "https://www.wowhead.com/wotlk",
}

DEFAULT_RANGES = {
    "classic": {"quest": (1, 10000), "item": (1, 25000), "npc": (1, 25000), "spell": (1, 70000), "object": (1, 250000)},
    "tbc": {"quest": (1, 12000), "item": (1, 36000), "npc": (1, 25000), "spell": (1, 70000), "object": (1, 250000)},
    "wotlk": {"quest": (1, 14000), "item": (1, 52000), "npc": (1, 36000), "spell": (1, 80000), "object": (1, 250000)},
}

def entity_url(expansion: str, entity_type: str, entity_id: int) -> str:
    return f"{URL_PREFIX[expansion]}/{entity_type}={entity_id}"

def export_path(expansion: str, entity_type: str) -> Path:
    return EXPORTS / f"{expansion}_{entity_type}.json"

def csv_path(expansion: str, entity_type: str) -> Path:
    return EXPORTS / f"{expansion}_{entity_type}.csv"

def cache_path(expansion: str, entity_type: str) -> Path:
    return CACHE / f"{expansion}_{entity_type}_checked.json"

def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)

def write_exports(expansion: str, entity_type: str, rows: Iterable[Dict[str, Any]]) -> None:
    rows = list(rows)
    out_json = export_path(expansion, entity_type)
    existing = load_json(out_json, [])
    by_key = {(str(r.get("type")), str(r.get("expansion")), int(r.get("id"))): r for r in existing if r.get("id") is not None}
    for r in rows:
        if r.get("id") is None:
            continue
        by_key[(str(r.get("type")), str(r.get("expansion")), int(r.get("id")))] = r
    merged = sorted(by_key.values(), key=lambda x: (str(x.get("expansion")), str(x.get("type")), int(x.get("id", 0))))
    save_json(out_json, merged)
    out_csv = csv_path(expansion, entity_type)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["expansion", "type", "id", "name", "url", "source", "meta"])
        writer.writeheader()
        for r in merged:
            writer.writerow({
                "expansion": r.get("expansion", ""),
                "type": r.get("type", ""),
                "id": r.get("id", ""),
                "name": r.get("name", ""),
                "url": r.get("url", ""),
                "source": r.get("source", ""),
                "meta": json.dumps(r.get("meta", {}), ensure_ascii=False),
            })
