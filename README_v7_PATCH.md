# WoW Database Explorer v7 patch

Copy these files over the current repo root.

What this patch changes:

- Removes the Settings button from the home page.
- Makes the portal home page fill the full screen.
- Adds subtle CSS fire movement in front of the portal statues.
- Adds subtle animated aura/shimmer around the three clickable expansion logo areas.
- Keeps the three portal logo areas clickable.
- Adds music support scaffolding.

## Music folder

Create/use this root folder:

```txt
music/
```

Use these filenames exactly:

```txt
music/homepage.mp3
music/vanilla.mp3
music/tbc.mp3
music/wotlk.mp3
music/settings.mp3
```

The app serves those files through `/music/<filename>`. It also accepts `.ogg`, `.wav`, and `.m4a` with the same base names if you do not use mp3.

There is a small Music button in the bottom-right corner. Browsers usually require a user click before sound can start, so the first click enables playback. After that, each page loads its own looped track; changing pages creates a fresh audio element, so that page track starts from the beginning.

Not included in this patch:

- actual music files
- all-data-specific music; the All Data page uses settings music if available
- skills/spells/achievements expansion
- deeper page redesign
