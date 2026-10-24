"""Dark mode on Windows 10: Qt picks the windowsvista style there, and it draws light even when the system is dark.
Fusion takes the system's dark palette, so the window then follows the system like on Windows 11 and Linux."""
from PySide6.QtCore import Qt


def pick_style(style, scheme):
    """Style to switch to for the current style name and colour scheme, or None to keep it."""
    if scheme == Qt.ColorScheme.Dark and style.lower() == "windowsvista":
        return "Fusion"
    return None


def apply(app):
    """Check once at start and again when the user switches the system between light and dark."""
    def check(scheme=None):
        s = pick_style(app.style().name(), app.styleHints().colorScheme() if scheme is None else scheme)
        if s:
            app.setStyle(s)
    check()
    app.styleHints().colorSchemeChanged.connect(check)
