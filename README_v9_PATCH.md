# WoW Database Explorer v9 patch

This patch is based on the current repository file names in `static/img`:

- `homepage.png`
- `homeicon.png`
- `settingsicon.png`
- `classicicon.png`
- `classiclogo.png`
- `tbcicon.png`
- `tbclogo.png`
- `wotlkicon.png`
- `wotlklogo.png`

No image files are included or overwritten in this patch.

## Fixes

- Home page uses the existing `homepage.png` portal image only.
- No extra logos are placed on top of the portal image.
- Invisible click areas are placed over the already-visible portal logos.
- Removed the floating Music button.
- Music controls are in Settings only.
- Music on/off and volume are saved in localStorage.
- All Expansions uses Classic icon + Classic logo as placeholder.
- All Expansions uses `all.mp3` only if it exists. It does not intentionally use Settings music.
- Expansion pages use their matching logo in the header.
- No fire/logo animations are included.
- Existing data/search/pagination logic is kept.

## How to apply

Copy these folders/files into the repository root and overwrite existing files:

```txt
app.py
templates/
static/style.css
README_v9_PATCH.md
```

Do not copy any image files from an older patch over your current `static/img` folder.
