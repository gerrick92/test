# WoW Database Explorer v10 patch

This patch fixes the issues reported after v9.

## What changed

- Restores the working transparent image assets, mapped to the current repo filenames.
- Keeps the current music system and Settings controls.
- Does not add fire/logo animations.
- Fixes the homepage portal click targets so the invisible links match the visible logos in the portal.
- Removes the visible All Expansions placeholder note from the header.
- Keeps All Expansions on Classic icon/logo placeholder for now.

## Files included

Copy the contents of `wow_v10_patch/` over the repo root. This patch includes:

```txt
app.py
templates/
static/style.css
static/img/
assets_preview_v10.png
README_v10_PATCH.md
```

No music files are included. Keep local music files in your own `music/` folder.
