# v2.4 pagination + item filters patch

Code-only patch. Does not touch your DB input files or SQLite DB.

Adds:
- First / Previous / Next / Last
- Numbered page buttons
- Jump to page
- Item group filters:
  - Cloth
  - Leather
  - Mail
  - Plate
  - Weapons
  - Jewelry
  - Trinkets
  - Consumables
  - Quest items
  - Misc
- Equipment slot filters:
  - Head
  - Chest
  - Legs
  - Feet
  - Hands
  - Ring
  - Trinket
  - Weapon

Copy files over your current project.

Then run:

python app.py

No re-import needed.
