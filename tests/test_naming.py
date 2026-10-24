import unittest
from altui_tool import naming


class BaseName(unittest.TestCase):
    CASES = [
        ("SlimBody_P.pak", "SlimBody"),
        ("FemaleOGMORPH-0.6_P.pak", "FemaleOGMORPH"),
        ("Jodithicctest4_P.pak", "Jodithicctest4"),
        ("BodyAltUI_Slim.pak", "Slim"),
        ("Body_Curvy.pak", "Curvy"),
        ("WeaponAltUI_Gold.pak", "Gold"),
        ("IdleAltUI_Calm.pak", "Calm"),
        ("Some Revolver v1.2.pak", "Some_Revolver"),
        ("Glock_v2.pak", "Glock"),
        ("SlimBody-996-1-2-1700000000.pak", "SlimBody"),
        ("TKA-UN_Dv1-fix1.3d.pak", "TKA_UN_Dv1_fix1_3d"),
        ("Jodi_Idle_Adjustment_P.pak", "Jodi_Idle_Adjustment"),
        ("Mod_2.pak", "Mod_2"),
        ("___.pak", "Mod"),
        ("ümlaut körper.PAK", "mlaut_k_rper"),
    ]

    def test_cases(self):
        for given, want in self.CASES:
            with self.subTest(given=given):
                self.assertEqual(naming.base_name(given), want)


class Title(unittest.TestCase):
    def test_title(self):
        self.assertEqual(naming.title_of("Some_Revolver"), "Some Revolver")
        self.assertEqual(naming.title_of("SlimBody"), "SlimBody")


class Valid(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(naming.valid("Slim_2"))
        self.assertFalse(naming.valid(""))
        self.assertFalse(naming.valid("Slim Body"))
        self.assertFalse(naming.valid("Körper"))
