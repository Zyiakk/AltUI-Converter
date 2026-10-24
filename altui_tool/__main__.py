"""Entry point: the window, or --selftest [<report file>] without one."""
import os, sys


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if sys.stdout is None:                      # windowed exe on Windows: no console
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")
    for stream in (sys.stdout, sys.stderr):     # a cp1252 console cannot take "→" and the like: replace, don't crash
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    if argv[:1] == ["--selftest"]:
        from altui_tool import selftest
        return selftest.run(argv[1] if len(argv) > 1 else None)
    from PySide6.QtWidgets import QApplication
    from altui_tool.i18n import tr
    from altui_tool.ui import theme
    from altui_tool.ui.main_window import MainWindow
    app = QApplication(sys.argv[:1])
    app.setApplicationName(tr("app.title"))
    theme.apply(app)
    w = MainWindow()
    w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
