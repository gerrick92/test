from __future__ import annotations

import argparse
import subprocess
import sys

PRESETS = {
    "classic": {
        "quest": (1, 9000),
        "item": (1, 70000),
        "npc": (1, 25000),
        "spell": (1, 60000),
        "object": (1, 20000),
    },
    "tbc": {
        "quest": (1, 12000),
        "item": (1, 40000),
        "npc": (1, 30000),
        "spell": (1, 70000),
        "object": (1, 25000),
    },
    "wotlk": {
        "quest": (1, 15000),
        "item": (1, 60000),
        "npc": (1, 40000),
        "spell": (1, 80000),
        "object": (1, 30000),
    },
}

CORE_TYPES = ["quest", "item", "npc", "spell"]
EXTENDED_TYPES = ["quest", "item", "npc", "spell", "object"]

def run(cmd: list[str]) -> None:
    print("\n" + "=" * 90)
    print("RUN:", " ".join(cmd))
    print("=" * 90)
    subprocess.run(cmd, check=True)

def parse_range(value: str) -> tuple[int, int]:
    if "-" not in value:
        raise argparse.ArgumentTypeError("Range must look like 1-9000")
    left, right = value.split("-", 1)
    return int(left), int(right)

def main() -> None:
    parser = argparse.ArgumentParser(description="Run resumable Wowhead ID scans using safe presets.")
    parser.add_argument("--expansion", choices=["classic", "tbc", "wotlk", "all"], required=True)
    parser.add_argument("--types", default="core", help="core, extended, all, or comma list like quest,item,npc,spell")
    parser.add_argument("--delay", type=float, default=0.35, help="Delay between requests. Be nice to Wowhead.")
    parser.add_argument("--range", type=parse_range, default=None, help="Override ID range, example: --range 1-2000")
    parser.add_argument("--build-db", action="store_true", help="Build SQLite DB after scan.")
    parser.add_argument("--dry-run", action="store_true", help="Only print what would run.")
    args = parser.parse_args()

    expansions = ["classic", "tbc", "wotlk"] if args.expansion == "all" else [args.expansion]
    if args.types == "core":
        types = CORE_TYPES
    elif args.types in {"extended", "all"}:
        types = EXTENDED_TYPES
    else:
        types = [t.strip() for t in args.types.split(",") if t.strip()]

    planned: list[list[str]] = []
    for expansion in expansions:
        for typ in types:
            if typ not in PRESETS[expansion] and args.range is None:
                print(f"SKIP: no preset range for {expansion} {typ}")
                continue
            start, end = args.range if args.range else PRESETS[expansion][typ]
            cmd = [
                sys.executable,
                "scripts/scan_wowhead_ids.py",
                "--expansion", expansion,
                "--type", typ,
                "--start", str(start),
                "--end", str(end),
                "--delay", str(args.delay),
            ]
            planned.append(cmd)

    print("Planned scans:")
    for cmd in planned:
        print("  " + " ".join(cmd))

    if args.dry_run:
        return
    for cmd in planned:
        run(cmd)
    if args.build_db:
        run([sys.executable, "scripts/build_database.py"])

if __name__ == "__main__":
    main()
