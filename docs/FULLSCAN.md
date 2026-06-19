# Fullscan guide

The normal listview export can hit Wowhead's 1000-row cap. Fullscan solves this by checking entity IDs directly and saving found pages locally.

## Fast sanity test

```powershell
python scripts\export_listviews.py --sample --debug
python scripts\build_database.py
python scripts\search_offline.py quest "Diplomat"
```

## Small scan test

```powershell
python scripts\scan_wowhead_ids.py --expansion classic --type quest --start 1 --end 200 --delay 0.25
python scripts\build_database.py
python scripts\search_offline.py quest "Diplomat"
```

## Classic full core scan

Core means quest, item, npc, spell.

```powershell
python scripts\scan_presets.py --expansion classic --types core --delay 0.35 --build-db
```

Shortcut:

```powershell
python scripts\quick_fullscan_classic.py
```

## Full Classic + TBC + WotLK core scan

This can take hours. It is resumable through cache.

```powershell
python scripts\scan_presets.py --expansion all --types core --delay 0.35 --build-db
```

Shortcut:

```powershell
python scripts\quick_fullscan_all.py
```

## Dry-run first

```powershell
python scripts\scan_presets.py --expansion all --types core --dry-run
```

Recommended delay: 0.35 - 1.0 seconds. Use a higher delay if Wowhead starts blocking or failing.
