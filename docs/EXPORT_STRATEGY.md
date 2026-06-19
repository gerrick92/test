# Export Strategy

The project intentionally uses two collection modes.

## Why listview alone is not enough

Wowhead database pages often embed listview data in JavaScript variables like `listviewquests`, `listviewitems`, or Listview instances. Some pages expose up to 1000 rows. Other general pages expose only category links or a very small DOM fallback, which is why earlier versions returned 7 items, 2 NPCs and 5 spells.

## Mode A: Listview export

Fast and useful where Wowhead exposes embedded data.

```powershell
python scripts\export_listviews.py --sample --debug
python scripts\export_listviews.py --debug
```

## Mode B: ID scan export

Slow but more complete. It visits Wowhead entity pages by ID and stores valid pages. It is resumable and cached.

```powershell
python scripts\scan_wowhead_ids.py --expansion classic --type quest --start 1 --end 10000 --delay 0.25
```

Use `Ctrl+C` safely. Progress is saved in `data/cache`.

## Suggested order

1. Run listview sample.
2. Build DB and confirm search works.
3. Scan one small ID range.
4. Scan larger ranges overnight.
5. Rebuild DB.

## Why delay matters

A full scan is many HTTP requests. Keep a delay. The point is to archive once and use the local DB offline later.
