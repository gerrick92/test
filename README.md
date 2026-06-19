# WoW Database Explorer v1.6

Goal: build a local/offline searchable database from Wowhead for Classic, TBC and WotLK.

This version has two export methods:

1. **Listview export** - fast, reads Wowhead embedded listview data where available.
2. **ID scan export** - slower but more complete, checks entity IDs one by one and caches results so it can resume.

MaNGOS helpers are included only as copy-paste helpers. They are not required as a data source.

## Install

```powershell
pip install -r requirements.txt
python -m playwright install chromium
```

## Recommended test run

```powershell
python scripts\export_listviews.py --sample --debug
python scripts\build_database.py
python scripts\search_offline.py quest "Diplomat"
```

## Full ID scan, safer/resumable way

Start small first:

```powershell
python scripts\scan_wowhead_ids.py --expansion classic --type quest --start 1 --end 200 --delay 0.25
python scripts\build_database.py
python scripts\search_offline.py quest "Diplomat"
```

Then larger:

```powershell
python scripts\scan_wowhead_ids.py --expansion classic --type quest --start 1 --end 10000 --delay 0.25
python scripts\scan_wowhead_ids.py --expansion classic --type item --start 1 --end 25000 --delay 0.25
python scripts\scan_wowhead_ids.py --expansion classic --type npc --start 1 --end 25000 --delay 0.25
python scripts\scan_wowhead_ids.py --expansion classic --type spell --start 1 --end 70000 --delay 0.25
```

TBC/WotLK examples:

```powershell
python scripts\scan_wowhead_ids.py --expansion tbc --type quest --start 1 --end 12000 --delay 0.25
python scripts\scan_wowhead_ids.py --expansion wotlk --type quest --start 1 --end 14000 --delay 0.25
```

## Resume behavior

The scanner writes cache files in:

```txt
data/cache/
```

If you stop it with Ctrl+C, run the same command again and it skips already checked IDs.

## Build database

```powershell
python scripts\build_database.py
```

## Offline search

```powershell
python scripts\search_offline.py quest "The Missing Diplomat"
python scripts\search_offline.py item "Thunderfury"
python scripts\search_offline.py npc "Ragnaros"
python scripts\search_offline.py spell "Frostbolt"
```

## Web app

```powershell
python app.py
```

Open:

```txt
http://127.0.0.1:5000
```

## Important

A complete ID scan can take hours because it is intentionally throttled. This is better than hammering Wowhead and getting blocked. The point is: download once, build SQLite, then search offline forever.


## v1.7 Fullscan Presets

This version keeps the fixed SQLite rebuild and adds easier fullscan commands.

### First test

```powershell
python scripts\export_listviews.py --sample --debug
python scripts\build_database.py
python scripts\search_offline.py quest "Diplomat"
```

### Small ID-scan test

```powershell
python scripts\scan_wowhead_ids.py --expansion classic --type quest --start 1 --end 200 --delay 0.25
python scripts\build_database.py
```

### Classic full core scan

```powershell
python scripts\scan_presets.py --expansion classic --types core --delay 0.35 --build-db
```

### Classic + TBC + WotLK core scan

```powershell
python scripts\scan_presets.py --expansion all --types core --delay 0.35 --build-db
```

Read `docs/FULLSCAN.md`.
