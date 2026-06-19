# WoW Database App v2.1

Fixed DB-source version.

## Put files here

```txt
data/input/vanilla/
data/input/tbc/
data/input/wotlk/
```

Accepted: `.sql`, `.sql.gz`, `.zip`.

## Run

```powershell
pip install -r requirements.txt
python scripts\import_db_dumps.py --all
python scripts\diagnose_db.py
python app.py
```

Open:

```txt
http://127.0.0.1:5000
```

The app can now browse a category without typing a search term.
