import os, shutil, tempfile, unittest
from altui_tool import detect, fixtures
from altui_tool.i18n import tr


class Detect(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, self.d, ignore_errors=True)

    def p(self, name):
        return os.path.join(self.d, name)

    def test_body(self):
        r = detect.detect(fixtures.body_pak(self.p("SlimBody_P.pak")))
        self.assertEqual((r.kind, r.blocking), ("body", False))

    def test_idle(self):
        r = detect.detect(fixtures.idle_pak(self.p("Idle_P.pak")))
        self.assertEqual((r.kind, r.blocking), ("idle", False))

    def test_idle_with_dependency_blocks(self):
        r = detect.detect(fixtures.idle_dep_pak(self.p("Idle_P.pak")))
        self.assertEqual((r.kind, r.blocking), ("idle", True))
        self.assertIn("imports other packages", r.message)

    def test_weapon_skin(self):
        r = detect.detect(fixtures.weapon_skin_pak(self.p("ump.pak")))
        self.assertEqual((r.kind, r.weapon, r.parts, r.blocking), ("weapon", "UMP45", ("skin",), False))
        self.assertFalse(r.needs_game_pak)

    def test_weapon_unknown_asks_for_the_weapon(self):
        r = detect.detect(fixtures.weapon_unknown_pak(self.p("knife.pak")))
        self.assertEqual((r.kind, r.weapon, r.blocking), ("weapon", None, False))
        self.assertEqual(r.message, tr("detect.pick_weapon"))

    def test_weapon_refused_by_the_converter_blocks(self):
        r = detect.detect(fixtures.weapon_normal_only_pak(self.p("normal.pak")))
        self.assertEqual((r.kind, r.blocking), ("weapon", True))
        self.assertIn("base colour", r.message)

    def test_unknown(self):
        r = detect.detect(fixtures.other_pak(self.p("other.pak")))
        self.assertEqual((r.kind, r.blocking), ("unknown", False))
        self.assertIn("/Game/Project/Something/Else", r.message)

    def test_garbage(self):
        with open(self.p("bad.pak"), "wb") as f:
            f.write(b"not a pak" * 50)
        r = detect.detect(self.p("bad.pak"))
        self.assertEqual((r.kind, r.blocking, r.message), ("unknown", True, tr("detect.unreadable")))

    def test_converted_paks_are_recognised(self):   # an AltUI pak dropped again: say so instead of "no weapon textures …"
        from altui_tool import jobs
        out = self.p("out")
        cases = (("body", fixtures.body_pak(self.p("B_P.pak")), {}),
                 ("weapon", fixtures.weapon_skin_pak(self.p("ump.pak")), {}),
                 ("idle", fixtures.idle_pak(self.p("I_P.pak")), {"altui_pak": fixtures.altui_pak(self.p("AltUI.pak"))}))
        for kind, src, kw in cases:
            res = jobs.execute(jobs.Job(kind, src, "Done", "Done", out, **kw))
            self.assertTrue(res.ok, res.summary)
            r = detect.detect(res.pak)
            self.assertEqual((r.kind, r.blocking), (kind, True))
            self.assertEqual(r.message, tr("detect.converted", kind=tr("kind." + kind)))

    def test_converted_needs_one_prefixed_folder(self):
        self.assertEqual(detect.converted(["/Game/Mod/Body_Thicc/Female", "/Game/Mod/Body_Thicc/Mod_BodyShape"]), "body")
        self.assertEqual(detect.converted(["/Game/Mod/WeaponAltUI_X/Mod_WeaponSkin"]), "weapon")
        self.assertIsNone(detect.converted(["/Game/Mod/Ankle/Mod_Clothes"]))                        # a clothes mod
        self.assertIsNone(detect.converted(["/Game/Mod/Body_X/A", "/Game/Mod/Other/B"]))            # two folders
        self.assertIsNone(detect.converted(["/Game/Mod/Body_X/A", "/Game/Project/Character/Jodi/Body/Female"]))
        self.assertIsNone(detect.converted([]))
