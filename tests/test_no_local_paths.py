"""Nothing that ships may carry a path of the build machine (/mnt/…, /home/…, C:\\Users\\…)."""
import os, re, unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "altui_tool")
LOCAL = re.compile(r"/mnt/|/home/|[A-Za-z]:\\+Users", re.I)


class NoLocalPaths(unittest.TestCase):
    def test_shipped_sources(self):
        hits = []
        for d, _, files in os.walk(ROOT):
            for f in files:
                if f.endswith((".py", ".txt")):
                    p = os.path.join(d, f)
                    with open(p, encoding="utf-8", errors="replace") as fh:
                        for n, line in enumerate(fh, 1):
                            if LOCAL.search(line):
                                hits.append("%s:%d: %s" % (os.path.relpath(p, ROOT), n, line.strip()))
        self.assertEqual(hits, [])
