"""The log: a tree whose lines wrap to the width of the window instead of being cut off with "…"."""
from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import QTextLayout, QTextOption
from PySide6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionViewItem, QTreeWidget

PAD = 3   # px above/below and right of the text


def _layout(text, font, width):
    """Lines broken at word boundaries, mid-word only when a word (a path) is wider than the line."""
    lay = QTextLayout(text, font)
    opt = QTextOption(); opt.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere); lay.setTextOption(opt)
    lay.beginLayout(); y = 0.0
    while True:
        line = lay.createLine()
        if not line.isValid():
            break
        line.setLineWidth(max(width, 1)); line.setPosition(QPointF(0, y)); y += line.height()
    lay.endLayout()
    return lay, y


class WrapDelegate(QStyledItemDelegate):
    def _text_width(self, index):
        view = self.parent()
        depth, p = 1, index.parent()
        while p.isValid():
            depth, p = depth + 1, p.parent()
        return view.viewport().width() - view.indentation() * depth - 2 * PAD

    def sizeHint(self, option, index):
        opt = QStyleOptionViewItem(option); self.initStyleOption(opt, index)
        _lay, h = _layout(opt.text, opt.font, self._text_width(index))
        return QSize(opt.rect.width(), int(h) + 2 * PAD)

    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option); self.initStyleOption(opt, index)
        text, opt.text = opt.text, ""
        opt.widget.style().drawControl(QStyle.CE_ItemViewItem, opt, painter, opt.widget)   # background, selection
        fg = index.data(Qt.ForegroundRole)
        if opt.state & QStyle.State_Selected:
            color = opt.palette.highlightedText().color()
        else:
            color = fg.color() if fg is not None else opt.palette.text().color()
        lay, _h = _layout(text, opt.font, opt.rect.width() - 2 * PAD)
        painter.save()
        painter.setPen(color)
        lay.draw(painter, QPointF(opt.rect.x() + PAD, opt.rect.y() + PAD))
        painter.restore()


class LogTree(QTreeWidget):
    """A log whose lines wrap to the width of the window instead of being cut off with "…"."""
    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True); self.setUniformRowHeights(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setItemDelegate(WrapDelegate(self))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.scheduleDelayedItemsLayout()   # row heights depend on the width
