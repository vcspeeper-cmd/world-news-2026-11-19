"""Copy the committed poster into the output directory for the make.fun harness."""

import os
import shutil
import sys


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, "entry.png")
    if not os.path.isfile(source):
        sys.stderr.write("entry.png is missing beside main.py\n")
        return 1
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "").strip() or "/output"
    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(source, os.path.join(out_dir, "entry.png"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
