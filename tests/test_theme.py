import os, unittest
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from altui_tool.ui import theme

APP = QApplication.instance() or QApplication([])
DARK, LIGHT, UNKNOWN = Qt.ColorScheme.Dark, Qt.ColorScheme.Light, Qt.ColorScheme.Unknown


class PickStyle(unittest.TestCase):
    """Windows 10 gets Qt's windowsvista style, which draws light whatever the system says - the window stayed light
    in dark mode. Windows 11 (windows11 style) and Linux follow the system themselves."""

    def test_windows10_dark_switches_to_fusion(self):
        self.assertEqual(theme.pick_style("windowsvista", DARK), "Fusion")

    def test_windows10_light_keeps_its_style(self):
        self.assertIsNone(theme.pick_style("windowsvista", LIGHT))
        self.assertIsNone(theme.pick_style("windowsvista", UNKNOWN))

    def test_styles_that_follow_the_system_stay(self):
        for style in ("windows11", "fusion", "Breeze", "kvantum"):
            self.assertIsNone(theme.pick_style(style, DARK), style)

    def test_apply_keeps_the_offscreen_style(self):   # no windowsvista here: apply changes nothing
        before = APP.style().name()
        theme.apply(APP)
        self.assertEqual(APP.style().name(), before)


if __name__ == "__main__": unittest.main()
