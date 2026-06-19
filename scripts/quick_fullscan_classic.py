from __future__ import annotations
import subprocess, sys

subprocess.run([
    sys.executable, "scripts/scan_presets.py",
    "--expansion", "classic",
    "--types", "core",
    "--delay", "0.35",
    "--build-db",
], check=True)
