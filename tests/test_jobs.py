import os, shutil, tempfile, unittest
from unittest import mock
from altui_tool import fixtures, jobs
from altui_tool.i18n import tr


class Execute(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, self.d, ignore_errors=True)
        self.out = os.path.join(self.d, "Mods")
        self.altui = fixtures.altui_pak(os.path.join(self.d, "AltUI.pak"))

    def job(self, kind, src, **kw):
        return jobs.Job(kind, src, "T", "T title", self.out, **kw)

    def test_body(self):
        r = jobs.execute(self.job("body", fixtures.body_pak(os.path.join(self.d, "B_P.pak"))))
        self.assertTrue(r.ok, r.summary)
        self.assertEqual(r.pak, os.path.join(self.out, "BodyAltUI_T.pak"))
        self.assertTrue(os.path.isfile(r.pak))
        self.assertEqual(r.summary, tr("log.ok", source="B_P.pak", pak="BodyAltUI_T.pak",
                                       size=jobs.human_size(os.path.getsize(r.pak))))
        self.assertEqual(r.details[:2], ["source: " + os.path.join(self.d, "B_P.pak"), "folder: " + self.out])
        self.assertIn("post-process blueprint: AltUI ABP_BodyScale (Body Shape sliders); defaults: all 1.0", r.details)

    def test_body_keep_abp(self):
        r = jobs.execute(self.job("body", fixtures.body_pak(os.path.join(self.d, "B_P.pak")), keep_abp=True))
        self.assertTrue(r.ok, r.summary)
        self.assertIn("post-process blueprint: the mod's own (no Body Shape sliders)", r.details)

    def test_weapon(self):
        r = jobs.execute(self.job("weapon", fixtures.weapon_skin_pak(os.path.join(self.d, "ump.pak"))))
        self.assertTrue(r.ok, r.summary)
        self.assertEqual(os.path.basename(r.pak), "WeaponAltUI_T.pak")
        self.assertIn("weapon: UMP45", r.details)

    def test_weapon_picked(self):
        r = jobs.execute(self.job("weapon", fixtures.weapon_unknown_pak(os.path.join(self.d, "k.pak")), weapon="Knife"))
        self.assertTrue(r.ok, r.summary)
        self.assertIn("weapon: Knife", r.details)

    def test_idle(self):
        r = jobs.execute(self.job("idle", fixtures.idle_pak(os.path.join(self.d, "I_P.pak")), altui_pak=self.altui))
        self.assertTrue(r.ok, r.summary)
        self.assertEqual(os.path.basename(r.pak), "IdleAltUI_T.pak")
        self.assertIn("templates: Catwalk_Normal, Normal_Normal", r.details)

    def test_idle_without_altui(self):
        r = jobs.execute(self.job("idle", fixtures.idle_pak(os.path.join(self.d, "I_P.pak"))))
        self.assertFalse(r.ok)
        self.assertEqual(r.summary, tr("log.failed", source="I_P.pak", kind=tr("kind.idle"), error=tr("hint.no_altui")))

    def test_existing_target_needs_force(self):
        src = fixtures.body_pak(os.path.join(self.d, "B_P.pak"))
        self.assertTrue(jobs.execute(self.job("body", src)).ok)
        r = jobs.execute(self.job("body", src))
        self.assertFalse(r.ok); self.assertIn("already exists", r.summary)
        self.assertTrue(jobs.execute(self.job("body", src, force=True)).ok)

    def test_refusal_names_source_and_type(self):
        src = fixtures.weapon_skin_pak(os.path.join(self.d, "ump.pak"))
        r = jobs.execute(self.job("body", src))
        self.assertFalse(r.ok)
        self.assertTrue(r.summary.startswith("ump.pak as Body: "), r.summary)
        self.assertEqual(r.details, ["source: " + src])

    def test_source_out_of_a_zip(self):
        j = self.job("body", os.path.join("tmp", "B_P.pak"), dropped=os.path.join("dl", "mods.zip"))
        self.assertEqual(jobs.source_name(j), "B_P.pak (mods.zip)")
        self.assertEqual(jobs.source_path(j), os.path.join("dl", "mods.zip") + " › B_P.pak")

    def test_internal_error(self):
        with mock.patch.object(jobs, "run", side_effect=ValueError("boom")):
            r = jobs.execute(self.job("body", "x.pak"))
        self.assertFalse(r.ok)
        self.assertEqual(r.summary, tr("log.failed", source="x.pak", kind=tr("kind.body"), error=tr("log.internal")))
        self.assertEqual(r.details[-1], "ValueError: boom")

    def test_weapon_details_keep_the_icon_apart(self):
        log = {"weapon": "Shotgun", "textures": {"Icon": "item_icons_shotgun"}, "meshes": ["SM_Shotgun"], "paints": [],
               "sound": None, "dropped": []}
        self.assertEqual(jobs.details("weapon", log), ["weapon: Shotgun", "item icon: item_icons_shotgun", "meshes: SM_Shotgun"])
        log["textures"] = {"MainTex": "T_BC", "NormalTex": "T_N", "Icon": "ic"}
        self.assertIn("skin textures: T_BC, T_N", jobs.details("weapon", log))

    def test_weapon_details_name_the_model_paints(self):
        log = {"weapon": "Glock", "textures": {}, "meshes": ["SK_SE"], "paints": ["M_Camo_Pistol"], "sound": None, "dropped": []}
        self.assertEqual(jobs.details("weapon", log), ["weapon: Glock", "meshes: SK_SE", "paints of the model: M_Camo_Pistol"])

    def test_target_path(self):
        j = jobs.Job("weapon", "x.pak", "A", "A", "out")
        self.assertEqual(jobs.target_path(j), os.path.join("out", "WeaponAltUI_A.pak"))


class Size(unittest.TestCase):
    def test_human_size(self):
        self.assertEqual(jobs.human_size(500), "500 B")
        self.assertEqual(jobs.human_size(1536), "1.5 KB")
        self.assertEqual(jobs.human_size(5 * 1024 * 1024), "5.0 MB")
