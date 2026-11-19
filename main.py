#!/usr/bin/env python3
"""make.fun entry point for "world-news-2026-11-19".

Copies the pre-rendered ``entry.png`` from this repository to
``/output/entry.png``.  Standard library only, no network, deterministic.
"""

from __future__ import annotations

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "entry.png")
OUTPUT_DIR = "/output"
DEST = os.path.join(OUTPUT_DIR, "entry.png")


def main() -> int:
    if not os.path.isfile(SOURCE):
        print(f"error: missing {SOURCE}", file=sys.stderr)
        return 1

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    shutil.copyfile(SOURCE, DEST)

    written = os.path.getsize(DEST)
    print(f"wrote {written} bytes to {DEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
