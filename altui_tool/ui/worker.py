"""Runs one job off the UI thread."""
from PySide6.QtCore import QThread, Signal
from altui_tool import jobs


class Worker(QThread):
    done = Signal(object)          # jobs.Result

    def __init__(self, job, parent=None):
        super().__init__(parent)
        self.job = job

    def run(self):
        self.done.emit(jobs.execute(self.job))
