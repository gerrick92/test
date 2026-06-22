# WoW Database Explorer v5 UI asset pass

This zip contains a rebuilt project package focused on the current front-end pass:

- fixed transparent expansion logos for the home page
- fixed transparent round icons for Vanilla, TBC and WotLK
- fixed the hearthstone home icon without destroying the stone
- kept icon sizes visually consistent in the UI
- removed the big expansion logos from inner expansion pages and used icons there instead
- pushed the UI closer to an old-school WoW website feel without copying login/account/forum clutter

## Run

```powershell
pip install -r requirements.txt
python app.py
```

Open:

```txt
http://127.0.0.1:5000
```

## Data folders

Put your DB dumps / local DB in the same structure as before.

```txt
data/input/vanilla/
data/input/tbc/
data/input/wotlk/
```

If `data/db/wow.db` already exists from your local project, the app will use it.

## Notes for this pass

Implemented now:
- transparent assets cleanup
- equal icon sizing
- icon-only expansion headers
- old-school WoW/private-server inspired layout direction

Still part of the broader direction:
- more Vanilla / TBC / WotLK specific page dressing over time
- further refinement of panels/backgrounds if needed after testing
