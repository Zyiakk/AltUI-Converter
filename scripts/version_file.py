"""Writes the Windows version resource for PyInstaller (--version-file) from altui_tool.__version__.
  python scripts/version_file.py <out file>"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from altui_tool import __version__

a, b, c = (int(x) for x in __version__.split("."))
TEXT = """VSVersionInfo(
  ffi=FixedFileInfo(filevers=({a}, {b}, {c}, 0), prodvers=({a}, {b}, {c}, 0), mask=0x3f, flags=0x0, OS=0x40004,
                    fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'AltUI'),
      StringStruct('FileDescription', 'AltUI Mod Converter'),
      StringStruct('FileVersion', '{v}'),
      StringStruct('InternalName', 'AltUIConverter'),
      StringStruct('LegalCopyright', 'GPL-3.0'),
      StringStruct('OriginalFilename', 'AltUIConverter.exe'),
      StringStruct('ProductName', 'AltUI Mod Converter'),
      StringStruct('ProductVersion', '{v}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""".format(a=a, b=b, c=c, v=__version__)

with open(sys.argv[1], "w", encoding="utf-8") as f:
    f.write(TEXT)
