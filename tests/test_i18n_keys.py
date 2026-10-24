"""Every tr() key used in the code exists, and the table has no dead keys."""
import os, re, unittest
from altui_tool.i18n import STRINGS

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "altui_tool")
DYNAMIC = {"kind.unknown", "kind.body", "kind.weapon", "kind.idle"}     # built as "kind." + k


class Keys(unittest.TestCase):
    def test_keys(self):
        used = set()
        for d, _, files in os.walk(ROOT):
            if "converters" in d:
                continue
            for f in files:
                if f.endswith(".py"):
                    with open(os.path.join(d, f), encoding="utf-8") as fh:
                        used |= set(re.findall(r'tr\("([a-z_]+\.[a-z_]+)"', fh.read()))
        self.assertEqual(sorted(used - set(STRINGS["en"])), [])
        self.assertEqual(sorted(set(STRINGS["en"]) - used - DYNAMIC), [])
