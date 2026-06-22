# WoW Database Explorer v12 homepage contain patch

This is a small homepage-only correction after v11.

## Changed

- The portal image is no longer zoomed/cropped like a `cover` background.
- The full portal composition stays visible.
- Empty space around the contained portal is filled with a dark blurred backdrop based on the same portal image.
- The portal image and invisible click targets still share the same coordinate system.
- No images are replaced.
- No music, database, search, pagination, Settings, or expansion-page logic is changed.

## Copy into repo root

Copy these files over the current repo:

```txt
static/style.css
templates/home.html
README_v12_HOMEPAGE_CONTAIN_PATCH.md
```

Do not copy old `static/img` folders from earlier patches.
