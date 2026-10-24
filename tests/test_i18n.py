import unittest
from altui_tool import i18n


class Tr(unittest.TestCase):
    def test_format(self):
        self.assertEqual(i18n.tr("weapon.auto", weapon="UMP45"), "auto (UMP45)")

    def test_falls_back_to_english(self):
        old = i18n.LANG
        try:
            i18n.LANG = "xx"
            self.assertEqual(i18n.tr("form.convert"), "Convert")
        finally:
            i18n.LANG = old
