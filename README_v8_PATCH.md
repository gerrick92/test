# WoW Database Explorer v8 patch

Copy these files into the root of the current repo.

## Included changes

- Removes the floating music button.
- Adds music on/off and volume slider in Settings.
- Saves music enabled/disabled and volume in `localStorage`.
- Keeps music on by default if the browser allows playback.
- Uses `/music/<page>.mp3` with support for `.ogg`, `.wav`, and `.m4a` fallback.
- Uses `all.mp3` for the All Expansions page if that file exists.
- Restores the home page to only the portal/logos, with no visible database info and no All Data link.
- Removes the Settings button from the home page.
- Makes each home page logo its own visible link so the full visible Classic/TBC/WotLK logo is clickable.
- Uses the Classic icon and Classic logo as temporary placeholders for All Expansions.
- Uses the expansion logo in the expansion page header instead of plain text.
- Does not add new UI animation.

## Expected music files

Place these in the repo `music/` folder:

```txt
music/homepage.mp3
music/vanilla.mp3
music/tbc.mp3
music/wotlk.mp3
music/settings.mp3
music/all.mp3
```

If you do not want `all.mp3`, the All Expansions page will simply not play music after all file extensions fail.
