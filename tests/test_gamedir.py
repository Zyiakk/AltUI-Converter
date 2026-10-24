import os, shutil, tempfile, unittest
from altui_tool import fixtures, gamedir


class GameDir(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, self.d, ignore_errors=True)
        self.steam = os.path.join(self.d, "Steam"); self.lib = os.path.join(self.d, "Games", "SteamLibrary")
        os.makedirs(os.path.join(self.steam, "steamapps"))
        with open(os.path.join(self.steam, "steamapps", "libraryfolders.vdf"), "w") as f:
            f.write('"libraryfolders"\n{\n\t"0"\n\t{\n\t\t"path"\t\t"%s"\n\t}\n\t"1"\n\t{\n\t\t"path"\t\t"%s"\n\t}\n}\n'
                    % (self.steam, self.lib))
        self.game = fixtures.game_tree(self.lib)

    def test_library_folders(self):
        self.assertEqual(gamedir.library_folders(self.steam), [self.steam, self.steam, self.lib])

    def test_library_folders_windows_escapes(self):
        root = os.path.join(self.d, "Win"); os.makedirs(os.path.join(root, "steamapps"))
        with open(os.path.join(root, "steamapps", "libraryfolders.vdf"), "w") as f:
            f.write('"libraryfolders" { "1" { "path" "D:\\\\Games\\\\SteamLibrary" } }')
        self.assertEqual(gamedir.library_folders(root), [root, "D:\\Games\\SteamLibrary"])

    def test_find_game_in_second_library(self):
        self.assertEqual(gamedir.find_game([self.steam]), self.game)

    def test_find_game_none(self):
        self.assertIsNone(gamedir.find_game([os.path.join(self.d, "nothing")]))

    def test_normalize(self):
        self.assertEqual(gamedir.normalize(self.game), self.game)
        self.assertEqual(gamedir.normalize(os.path.join(self.game, "TheKillingAntidote")), self.game)
        self.assertIsNone(gamedir.normalize(self.d))
        self.assertIsNone(gamedir.normalize(""))

    def test_paths(self):
        p = gamedir.paths(self.game)
        inner = os.path.join(self.game, "TheKillingAntidote")
        self.assertEqual(p.mods, os.path.join(inner, "Mods"))
        self.assertEqual(p.altui_pak, os.path.join(inner, "Mods", "AltUI.pak"))
        self.assertEqual(p.pakchunk0, os.path.join(inner, "Content", "Paks", "pakchunk0-WindowsNoEditor.pak"))

    def test_paths_without_altui(self):
        os.remove(os.path.join(self.game, "TheKillingAntidote", "Mods", "AltUI.pak"))
        self.assertIsNone(gamedir.paths(self.game).altui_pak)

    def test_paths_none(self):
        self.assertEqual(gamedir.paths(None), gamedir.GamePaths())

    def test_steam_roots_are_strings(self):
        self.assertTrue(all(isinstance(r, str) for r in gamedir.steam_roots()))
