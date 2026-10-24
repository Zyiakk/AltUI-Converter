"""PyInstaller entry (a plain script: PyInstaller does not run a package's __main__ with its imports)."""
import sys
from altui_tool.__main__ import main

sys.exit(main())
