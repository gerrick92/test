# v2.2 code-only patch

This zip contains code only. It does not include DB files.

Copy these files over your current project. Keep your existing:

data/input/vanilla/
data/input/tbc/
data/input/wotlk/

Then run:

python scripts\import_db_dumps.py --all
python scripts\diagnose_db.py
python app.py

Main fix:
- Better quest_template import
- Full_DB-only import by default
- Browse without typing
- Sort by ID/name
- Diagnostics for quest counts
