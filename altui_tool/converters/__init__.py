"""The converters of AltUI (a release, or the development state for a dev build), copied unchanged by
scripts/sync_converters.sh - never edit them here.
They import each other flat (import bodypak), so this folder goes onto sys.path."""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def source_info():
    """The AltUI version the copies come from (first line of SOURCE.txt: "AltUI 2.6.0", dev build "AltUI 2.6.0+dev.<commit>"),
    for the About box and bug reports."""
    try:
        with open(os.path.join(HERE, "SOURCE.txt"), encoding="utf-8") as f:
            return f.readline().strip() or "unknown"
    except OSError:
        return "unknown"
