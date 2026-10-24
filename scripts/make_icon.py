"""Draws the app icon: altui_tool/assets/icon.png (window) and icon.ico (Windows exe). Run once; the results are committed.
  .venv/bin/python scripts/make_icon.py"""
import os, struct, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "altui_tool", "assets")


def draw(size):
    img = QImage(size, size, QImage.Format_ARGB32); img.fill(Qt.transparent)
    p = QPainter(img); p.setRenderHint(QPainter.Antialiasing)
    m = size * 0.04
    p.setPen(Qt.NoPen); p.setBrush(QColor("#2b5797"))
    p.drawRoundedRect(QRectF(m, m, size - 2 * m, size - 2 * m), size * 0.18, size * 0.18)
    f = QFont(); f.setBold(True); f.setPixelSize(int(size * 0.62))
    p.setFont(f); p.setPen(QColor("white"))
    p.drawText(QRectF(0, 0, size, size), Qt.AlignCenter, "A")
    p.end()
    return img


def png_bytes(img):
    ba = QByteArray(); buf = QBuffer(ba); buf.open(QIODevice.WriteOnly); img.save(buf, "PNG")
    return bytes(ba)


def main():
    app = QGuiApplication(sys.argv)  # noqa: F841  (fonts need an application)
    os.makedirs(OUT, exist_ok=True)
    draw(256).save(os.path.join(OUT, "icon.png"))
    sizes = (16, 32, 48, 256)
    pngs = [png_bytes(draw(s)) for s in sizes]
    head = struct.pack("<HHH", 0, 1, len(sizes))
    off = 6 + 16 * len(sizes); entries = b""
    for s, data in zip(sizes, pngs):          # ICO with PNG images inside (Vista and later)
        entries += struct.pack("<BBBBHHII", s % 256, s % 256, 0, 0, 1, 32, len(data), off); off += len(data)
    with open(os.path.join(OUT, "icon.ico"), "wb") as f:
        f.write(head + entries + b"".join(pngs))


if __name__ == "__main__":
    main()
