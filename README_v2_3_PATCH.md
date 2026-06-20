# v2.3 pagination/search patch

Code-only patch. Does not touch DB input files.

Fixes:
- Browse pages with Next / Previous
- No more hard-stop at first 200 rows
- Shows current page and total matching results
- Better search fallback using LIKE
- Numeric search can match exact ID

Copy files over your current project.

Then run:

python app.py

No need to re-import DB unless you changed data.
