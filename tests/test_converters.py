"""The vendored converters import as a set and know where they come from."""
import unittest
from altui_tool import converters


class Vendored(unittest.TestCase):
    def test_flat_imports(self):
        import bodypak, weaponpak, idlepak, idle_mods, weapon_skins, bodybones  # noqa: F401
        from pakio import open_pak  # noqa: F401
        self.assertTrue(callable(bodypak.convert) and callable(weaponpak.convert) and callable(idlepak.convert))

    def test_source_info(self):
        self.assertRegex(converters.source_info(), r"^AltUI \d+\.\d+\.\d+(\+dev\.[0-9a-f]+(\.dirty)?)?$")   # release or dev build, never a repo path
