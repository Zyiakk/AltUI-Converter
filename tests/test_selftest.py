import os, subprocess, sys, tempfile, unittest
from altui_tool import selftest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


class SelfTest(unittest.TestCase):
    def test_run_passes_and_reports(self):
        with tempfile.TemporaryDirectory() as d:
            report = os.path.join(d, "r.txt")
            self.assertEqual(selftest.run(report), 0)
            with open(report, encoding="utf-8") as f:
                text = f.read()
        self.assertIn("OK body", text); self.assertIn("OK weapon", text); self.assertIn("OK idle", text)
        self.assertIn("OK aes", text)   # game pak decryption (weapon with a shot sound) without cryptography
        self.assertTrue(text.rstrip().endswith("selftest passed"))

    def test_entry_point(self):
        r = subprocess.run([sys.executable, "run_app.py", "--selftest"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("selftest passed", r.stdout)

    def test_entry_point_on_a_cp1252_console(self):   # a Windows console: a pak name it cannot show must not crash it
        code = ("from altui_tool import __main__, selftest\n"
                "selftest.run = lambda report: print('HK416_\u7194\u5ca9_0_qhlys_P.pak') or 0\n"
                "raise SystemExit(__main__.main(['--selftest']))")
        env = dict(os.environ, PYTHONIOENCODING="cp1252")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, env=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stdout.strip(), b"HK416_??_0_qhlys_P.pak")
