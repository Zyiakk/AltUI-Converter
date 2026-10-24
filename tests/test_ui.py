import os, shutil, tempfile, unittest, zipfile
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from altui_tool import fixtures
from altui_tool.i18n import tr
from altui_tool.ui.main_window import MainWindow

APP = QApplication.instance() or QApplication([])


class Window(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, self.d, ignore_errors=True)
        self.game = fixtures.game_tree(os.path.join(self.d, "steam"))
        self.mods = os.path.join(self.game, "TheKillingAntidote", "Mods")
        self.w = self.make(lambda: self.game)

    def make(self, finder):
        ini = tempfile.mkstemp(dir=self.d, suffix=".ini")[1]
        w = MainWindow(settings=QSettings(ini, QSettings.IniFormat), game_finder=finder)
        self.addCleanup(w.close)
        return w

    def run_convert(self, w):
        w.convert_button.click()
        if w.worker is not None:
            w.worker.wait()
        APP.processEvents()

    def body(self, name="SlimBody_P.pak"):
        return fixtures.body_pak(os.path.join(self.d, name))

    def test_body_drop_prefills(self):
        self.w.load_source(self.body())
        self.assertEqual(self.w.kind(), "body")
        self.assertEqual(self.w.prefix_label.text(), "BodyAltUI_")
        self.assertEqual(self.w.name_edit.text(), "SlimBody")
        self.assertEqual(self.w.title_edit.text(), "SlimBody")
        self.assertEqual(self.w.out_edit.text(), self.mods)
        self.assertTrue(self.w.convert_button.isEnabled(), self.w.hint.text())

    def test_convert_writes_into_mods(self):
        self.w.load_source(self.body())
        self.run_convert(self.w)
        self.assertTrue(os.path.isfile(os.path.join(self.mods, "BodyAltUI_SlimBody.pak")))
        self.assertTrue(self.w.log.topLevelItem(0).text(0).startswith("✓"))
        self.assertTrue(self.w.convert_button.isEnabled())

    def test_existing_target_asks(self):
        self.w.load_source(self.body())
        self.run_convert(self.w)
        asked = []
        self.w.confirm_overwrite = lambda p: asked.append(p) or False
        self.run_convert(self.w)
        self.assertEqual(asked, [os.path.join(self.mods, "BodyAltUI_SlimBody.pak")])
        self.assertEqual(self.w.log.topLevelItemCount(), 1)

    def test_title_follows_name_until_edited(self):
        self.w.load_source(self.body())
        self.w.name_edit.setText("Curvy")
        self.assertEqual(self.w.title_edit.text(), "Curvy")
        QTest.keyClicks(self.w.title_edit, "!")
        self.w.name_edit.setText("Other")
        self.assertEqual(self.w.title_edit.text(), "Curvy!")

    def test_bad_name_blocks(self):
        self.w.load_source(self.body())
        self.w.name_edit.setText("")
        self.assertFalse(self.w.convert_button.isEnabled())
        self.assertEqual(self.w.hint.text(), tr("hint.bad_name"))

    def test_idle_needs_altui(self):
        w = self.make(lambda: None)
        w.out_edit.setText(self.d)
        w.load_source(fixtures.idle_pak(os.path.join(self.d, "Idle_P.pak")))
        self.assertEqual(w.kind(), "idle")
        self.assertFalse(w.convert_button.isEnabled())
        self.assertEqual(w.hint.text(), tr("hint.no_altui"))

    def test_idle_converts_with_the_game_altui(self):
        self.w.load_source(fixtures.idle_pak(os.path.join(self.d, "Calm_P.pak")))
        self.run_convert(self.w)
        self.assertTrue(os.path.isfile(os.path.join(self.mods, "IdleAltUI_Calm.pak")))

    def test_weapon_must_be_picked(self):
        self.w.load_source(fixtures.weapon_unknown_pak(os.path.join(self.d, "knife.pak")))
        self.assertEqual(self.w.kind(), "weapon")
        self.assertFalse(self.w.convert_button.isEnabled())
        self.w.weapon_combo.setCurrentIndex(self.w.weapon_combo.findData("Knife"))
        self.assertTrue(self.w.convert_button.isEnabled(), self.w.hint.text())

    def test_unknown_lets_the_user_pick(self):
        self.w.load_source(fixtures.other_pak(os.path.join(self.d, "other.pak")))
        self.assertIsNone(self.w.kind())
        self.assertFalse(self.w.convert_button.isEnabled())
        self.w.kind_combo.setCurrentIndex(self.w.kind_combo.findData("body"))
        self.assertTrue(self.w.convert_button.isEnabled())

    def test_zip_with_two_paks_asks_and_cleans_up(self):
        z = os.path.join(self.d, "mods.zip")
        with zipfile.ZipFile(z, "w") as zf:
            zf.write(self.body("A_P.pak"), "variants/A_P.pak")
            zf.write(fixtures.idle_pak(os.path.join(self.d, "B_P.pak")), "variants/B_P.pak")
        self.w.choose_pak = lambda names: names[1]
        self.w.load_source(z)
        self.assertEqual((self.w.kind(), self.w.name_edit.text()), ("idle", "B"))
        tmp = self.w.tmp
        self.assertTrue(os.path.isdir(tmp))
        self.w.close()
        self.assertFalse(os.path.exists(tmp))

    def test_two_files_are_refused(self):
        self.w.on_picked(["a.pak", "b.pak"])
        self.assertIsNone(self.w.src)
        self.assertEqual(self.w.log.topLevelItem(0).text(0), "✗ " + tr("drop.one_only"))

    def test_game_folder_is_remembered(self):
        ini = tempfile.mkstemp(dir=self.d, suffix=".ini")[1]
        w = MainWindow(settings=QSettings(ini, QSettings.IniFormat), game_finder=lambda: None)
        w.set_game_dir(os.path.join(self.game, "TheKillingAntidote"))
        w.close()
        w2 = MainWindow(settings=QSettings(ini, QSettings.IniFormat), game_finder=lambda: None)
        self.addCleanup(w2.close)
        self.assertEqual(w2.game.root, self.game)


class Log(unittest.TestCase):
    def test_long_lines_wrap_and_reflow(self):   # no "…": a narrow window gets more lines, a wider one fewer
        from PySide6.QtWidgets import QTreeWidgetItem
        from altui_tool.ui.log_view import LogTree
        t = LogTree(); self.addCleanup(t.close)
        long_ = QTreeWidgetItem(["post-process blueprint: defaults: " + ", ".join("Bone%d=1.00/1.05/1.06" % i for i in range(12))])
        path = QTreeWidgetItem(["source: " + "/x" * 3 + "/" + "a" * 200 + ".pak"])   # one word, wider than the line
        short = QTreeWidgetItem(["short"])
        for it in (long_, path, short):
            t.addTopLevelItem(it)
        t.resize(300, 400); t.show(); APP.processEvents()
        one = t.visualItemRect(short).height()
        narrow = t.visualItemRect(long_).height(), t.visualItemRect(path).height()
        self.assertGreater(narrow[0], 2 * one); self.assertGreater(narrow[1], 2 * one)
        t.resize(1200, 400); APP.processEvents(); t.doItemsLayout()
        self.assertLess(t.visualItemRect(long_).height(), narrow[0])
