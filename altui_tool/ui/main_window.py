"""The one window: game folder, drop area, the form for the dropped mod, Convert, log."""
import os, shutil, tempfile
from PySide6.QtCore import QRegularExpression, QSettings, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QRegularExpressionValidator
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QInputDialog, QLabel,
                               QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton, QStackedWidget,
                               QTreeWidgetItem, QVBoxLayout, QWidget)
from altui_tool import __version__, converters, detect, gamedir, inputs, jobs, naming
from altui_tool.i18n import tr
from altui_tool.ui.log_view import LogTree
from altui_tool.ui.worker import Worker
import weapon_skins

ICON = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
OK_COLOR, ERR_COLOR = QColor("#2e7d32"), QColor("#c62828")
PAGES = {"body": 0, "weapon": 1, "idle": 2}   # option pages; 3 = none (type not chosen)


class DropArea(QFrame):
    """Takes dropped files, or opens a file dialog on click."""
    picked = Signal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(90)
        self.setCursor(Qt.PointingHandCursor)
        lay = QVBoxLayout(self)
        label = QLabel(tr("drop.hint")); label.setAlignment(Qt.AlignCenter)
        lay.addWidget(label)
        self._style(False)

    def _style(self, active):
        self.setStyleSheet("DropArea { border: 2px dashed palette(%s); border-radius: 8px; }" % ("highlight" if active else "mid"))

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction(); self._style(True)

    def dragLeaveEvent(self, e):
        self._style(False)

    def dropEvent(self, e):
        self._style(False)
        self.picked.emit([u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()])

    def mousePressEvent(self, e):
        path, _ = QFileDialog.getOpenFileName(self, tr("drop.pick_title"), "", tr("drop.filter"))
        if path:
            self.picked.emit([path])


class MainWindow(QMainWindow):
    def __init__(self, settings=None, game_finder=gamedir.find_game):
        super().__init__()
        self.settings = settings or QSettings("AltUI", "AltUIConverter")
        self.src = self.tmp = self.dropped = self.detection = self.worker = None
        self.game = gamedir.GamePaths()
        self._running = False
        self._title_auto = True     # the title follows the name until the user types into it
        self._out_auto = True       # the output follows the game's Mods/ until the user picks another folder
        self.setWindowTitle("%s %s" % (tr("app.title"), __version__))
        if os.path.isfile(ICON):
            self.setWindowIcon(QIcon(ICON))
        self._build()
        geo = self.settings.value("geometry")
        if geo is not None:
            self.restoreGeometry(geo)
        else:
            self.resize(760, 680)
        saved_out = self.settings.value("out_dir", "")
        if saved_out and os.path.isdir(saved_out):
            self.out_edit.setText(saved_out); self._out_auto = False
        self.set_game_dir(gamedir.normalize(self.settings.value("game_dir", "")) or game_finder() or "", remember=False)

    # --- layout -------------------------------------------------------------------------------------------------
    def _build(self):
        central = QWidget(); self.setCentralWidget(central)
        root = QVBoxLayout(central)

        row = QHBoxLayout(); row.addWidget(QLabel(tr("game.label")))
        self.game_edit = QLineEdit(); self.game_edit.setReadOnly(True); row.addWidget(self.game_edit, 1)
        b = QPushButton(tr("game.browse")); b.clicked.connect(self.browse_game); row.addWidget(b)
        root.addLayout(row)
        self.game_status = QLabel(); root.addWidget(self.game_status)

        self.drop = DropArea(); self.drop.picked.connect(self.on_picked); root.addWidget(self.drop)

        form = QGridLayout(); r = 0
        form.addWidget(QLabel(tr("form.source")), r, 0)
        self.src_label = QLabel("-"); form.addWidget(self.src_label, r, 1, 1, 3); r += 1
        form.addWidget(QLabel(tr("form.type")), r, 0)
        self.kind_combo = QComboBox(); self.kind_combo.addItem(tr("kind.unknown"), None)
        for k in detect.KINDS:
            self.kind_combo.addItem(tr("kind." + k), k)
        form.addWidget(self.kind_combo, r, 1)
        self.detected_label = QLabel(); form.addWidget(self.detected_label, r, 2, 1, 2); r += 1
        form.addWidget(QLabel(tr("form.name")), r, 0)
        name_row = QHBoxLayout(); self.prefix_label = QLabel(); name_row.addWidget(self.prefix_label)
        self.name_edit = QLineEdit()
        self.name_edit.setValidator(QRegularExpressionValidator(QRegularExpression("[A-Za-z0-9_]*")))
        name_row.addWidget(self.name_edit, 1); form.addLayout(name_row, r, 1)
        form.addWidget(QLabel(tr("form.title")), r, 2)
        self.title_edit = QLineEdit(); form.addWidget(self.title_edit, r, 3)
        root.addLayout(form)

        self.pages = QStackedWidget()
        self.keep_abp = QCheckBox(tr("body.keep_abp")); self.pages.addWidget(self.keep_abp)
        wp = QWidget(); wl = QHBoxLayout(wp); wl.setContentsMargins(0, 0, 0, 0)
        wl.addWidget(QLabel(tr("weapon.label")))
        self.weapon_combo = QComboBox(); self.weapon_combo.addItem(tr("weapon.pick"), None)
        for w in weapon_skins.WEAPONS:
            self.weapon_combo.addItem(w, w)
        wl.addWidget(self.weapon_combo); wl.addStretch(1); self.pages.addWidget(wp)
        self.altui_label = QLabel(); self.pages.addWidget(self.altui_label)
        self.pages.addWidget(QWidget())
        root.addWidget(self.pages)

        row = QHBoxLayout(); row.addWidget(QLabel(tr("form.output")))
        self.out_edit = QLineEdit(); row.addWidget(self.out_edit, 1)
        b = QPushButton(tr("form.change")); b.clicked.connect(self.browse_output); row.addWidget(b)
        root.addLayout(row)

        self.hint = QLabel(); self.hint.setWordWrap(True); root.addWidget(self.hint)

        row = QHBoxLayout()
        self.overwrite = QCheckBox(tr("form.overwrite")); row.addWidget(self.overwrite); row.addStretch(1)
        self.busy = QProgressBar(); self.busy.setRange(0, 0); self.busy.setMaximumWidth(120); self.busy.hide()
        row.addWidget(self.busy)
        self.convert_button = QPushButton(tr("form.convert")); self.convert_button.setDefault(True)
        self.convert_button.clicked.connect(self.convert); row.addWidget(self.convert_button)
        root.addLayout(row)

        self.log = LogTree(); root.addWidget(self.log, 1)
        row = QHBoxLayout()
        b = QPushButton(tr("log.copy")); b.clicked.connect(self.copy_details); row.addWidget(b); row.addStretch(1)
        b = QPushButton(tr("form.about")); b.clicked.connect(self.about); row.addWidget(b)
        root.addLayout(row)

        # connected last: every handler may touch every widget
        self.kind_combo.currentIndexChanged.connect(self.on_kind_changed)
        self.name_edit.textChanged.connect(self.on_name_changed)
        self.title_edit.textEdited.connect(self.on_title_edited)
        self.weapon_combo.currentIndexChanged.connect(self.refresh)
        self.out_edit.textChanged.connect(self.refresh)
        self.out_edit.textEdited.connect(self.on_out_edited)
        self.on_kind_changed()

    # --- game folder and output ---------------------------------------------------------------------------------
    def set_game_dir(self, path, remember=True):
        root = gamedir.normalize(path)
        self.game = gamedir.paths(root)
        self.game_edit.setText(root or path)
        if root:
            self.game_status.setText(tr("game.found")); self.game_status.setStyleSheet("color: %s" % OK_COLOR.name())
            if remember:
                self.settings.setValue("game_dir", root)
            if self._out_auto:
                self.out_edit.setText(self.game.mods)
        else:
            self.game_status.setText(tr("game.invalid") if path else tr("game.missing"))
            self.game_status.setStyleSheet("color: %s" % ERR_COLOR.name())
        self.altui_label.setText(tr("idle.altui_found") if self.game.altui_pak else tr("idle.altui_missing"))
        self.refresh()

    def browse_game(self):
        d = QFileDialog.getExistingDirectory(self, tr("game.pick_title"), self.game.root or "")
        if d:
            self.set_game_dir(d)

    def browse_output(self):
        d = QFileDialog.getExistingDirectory(self, tr("form.output"), self.out_edit.text())
        if d:
            self.out_edit.setText(d); self.on_out_edited(d)

    def on_out_edited(self, text):
        self._out_auto = False
        self.settings.setValue("out_dir", text)

    # --- source ---------------------------------------------------------------------------------------------------
    def kind(self):
        return self.kind_combo.currentData()

    def on_picked(self, paths):
        if len(paths) != 1:
            self.add_log(False, tr("drop.one_only"), [])
            return
        self.load_source(paths[0])

    def load_source(self, path):
        self._drop_tmp()
        tmp = tempfile.mkdtemp(prefix="altui-conv-") if path.lower().endswith(".zip") else None
        try:
            pak = inputs.resolve(path, self.choose_pak, tmp)
        except inputs.InputError as e:
            pak = None
            self.add_log(False, "%s: %s" % (os.path.basename(path), e), [])
        if pak is None:
            if tmp:
                shutil.rmtree(tmp, ignore_errors=True)
            return
        self.tmp, self.src, self.dropped = tmp, pak, path if tmp else None
        shown = os.path.basename(pak)
        self.src_label.setText(shown if tmp is None else "%s  (%s)" % (shown, os.path.basename(path)))
        self.detection = d = detect.detect(pak)
        self.detected_label.setText(tr("form.detected", kind=tr("kind." + d.kind)))
        self.weapon_combo.setItemText(0, tr("weapon.auto", weapon=d.weapon) if d.weapon else tr("weapon.pick"))
        self.weapon_combo.setCurrentIndex(0)
        self.keep_abp.setChecked(False)
        self.kind_combo.setCurrentIndex(detect.KINDS.index(d.kind) + 1 if d.kind in detect.KINDS else 0)
        self._title_auto = True
        self.name_edit.setText(naming.base_name(shown))
        self.on_kind_changed()

    def choose_pak(self, names):
        name, ok = QInputDialog.getItem(self, tr("input.choose_title"), tr("input.choose_label"), names, 0, False)
        return name if ok else None

    def _drop_tmp(self):
        if self.tmp:
            shutil.rmtree(self.tmp, ignore_errors=True)
        self.tmp = None

    # --- form -------------------------------------------------------------------------------------------------------
    def on_kind_changed(self, *_):
        k = self.kind()
        self.prefix_label.setText(naming.PREFIXES.get(k, ""))
        self.pages.setCurrentIndex(PAGES.get(k, 3))
        self.refresh()

    def on_name_changed(self, text):
        if self._title_auto:
            self.title_edit.setText(naming.title_of(text))
        self.refresh()

    def on_title_edited(self, _text):
        self._title_auto = False

    def problem(self):
        """Why Convert is off; None when it is on."""
        k, d = self.kind(), self.detection
        if self._running:
            return ""
        if not self.src:
            return tr("hint.drop_first")
        if k is None:
            return d.message if d and d.message else tr("hint.pick_type")
        if not naming.valid(self.name_edit.text()):
            return tr("hint.bad_name")
        if not self.out_edit.text().strip():
            return tr("hint.no_output")
        if d and d.kind == k and d.blocking:
            return d.message
        if k == "idle" and not self.game.altui_pak:
            return tr("hint.no_altui")
        if k == "weapon" and self.weapon_combo.currentData() is None and not (d and d.kind == "weapon" and d.weapon):
            return tr("hint.pick_weapon")
        return None

    def refresh(self, *_):
        p, d = self.problem(), self.detection
        self.convert_button.setEnabled(p is None)
        if p is not None:
            self.hint.setText(p)
        elif self.kind() == "weapon" and d and d.needs_game_pak and not self.game.pakchunk0:
            self.hint.setText(tr("hint.no_pakchunk"))
        else:
            self.hint.setText(d.message if d and d.kind == self.kind() else "")

    # --- convert ----------------------------------------------------------------------------------------------------
    def make_job(self):
        name = self.name_edit.text()
        return jobs.Job(kind=self.kind(), src=self.src, name=name,
                        title=self.title_edit.text().strip() or naming.title_of(name),
                        out_dir=self.out_edit.text().strip(), force=self.overwrite.isChecked(),
                        keep_abp=self.keep_abp.isChecked(), weapon=self.weapon_combo.currentData(),
                        game_pak=self.game.pakchunk0, altui_pak=self.game.altui_pak, dropped=self.dropped)

    def confirm_overwrite(self, path):
        return QMessageBox.question(self, tr("overwrite.title"), tr("overwrite.text", path=path)) == QMessageBox.Yes

    def convert(self):
        if self.problem() is not None:
            return
        job = self.make_job()
        target = jobs.target_path(job)
        if os.path.exists(target) and not job.force:
            if not self.confirm_overwrite(target):
                return
            job.force = True
        self.worker = Worker(job, self)
        self.worker.done.connect(self.on_done)
        self._running = True
        self.set_busy(True)
        self.worker.start()

    def set_busy(self, on):
        for w in (self.drop, self.kind_combo, self.name_edit, self.title_edit, self.pages, self.out_edit, self.overwrite):
            w.setEnabled(not on)
        self.busy.setVisible(on)
        self.refresh()

    def on_done(self, result):
        self._running = False
        self.set_busy(False)
        self.add_log(result.ok, result.summary, result.details)

    # --- log ----------------------------------------------------------------------------------------------------------
    def add_log(self, ok, summary, details):
        item = QTreeWidgetItem([("✓ " if ok else "✗ ") + summary])
        item.setForeground(0, OK_COLOR if ok else ERR_COLOR)
        for line in details:
            item.addChild(QTreeWidgetItem([line]))
        self.log.addTopLevelItem(item)
        self.log.setCurrentItem(item)
        self.log.scrollToItem(item)
        if not ok and details:
            item.setExpanded(True)

    def copy_details(self):
        item = self.log.currentItem()
        if item is None:
            return
        top = item.parent() or item
        lines = [top.text(0)] + ["  " + top.child(i).text(0) for i in range(top.childCount())]
        lines += ["", "%s %s, %s" % (tr("app.title"), __version__, converters.source_info())]
        QGuiApplication.clipboard().setText("\n".join(lines))

    def about(self):
        QMessageBox.about(self, tr("about.title"), tr("about.text", version=__version__, source=converters.source_info()))

    def closeEvent(self, e):
        if self.worker is not None:
            self.worker.wait()
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.sync()
        self._drop_tmp()
        super().closeEvent(e)
