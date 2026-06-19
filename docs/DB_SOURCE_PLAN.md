# DB Source Plan

## v2 goal

Use CMaNGOS-style DB dumps as source of truth.

## Expansions

- Vanilla / Classic
- TBC
- WotLK

## Core tables

| App type | DB table |
|---|---|
| item | item_template |
| quest | quest_template |
| npc | creature_template |
| object | gameobject_template |

## Later relation tables

| Relation | DB table |
|---|---|
| NPC vendors | npc_vendor |
| NPC trainers | npc_trainer |
| Creature loot | creature_loot_template |
| GameObject loot | gameobject_loot_template |
| Quest starts | creature_questrelation |
| Quest ends | creature_involvedrelation |

## Why this is better than scraping Wowhead

- No 1000-row cap.
- No page blocking.
- IDs match MaNGOS.
- Faster import once dump exists locally.
- Better for GM/admin tools.
