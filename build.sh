#!/bin/bash
# Builds dist/AltUIConverter (Linux) and dist/AltUIConverter.exe (Windows: PyInstaller under Wine), then runs --selftest on both.
#   ./build.sh --setup          .venv with PySide6 + PyInstaller (once)
#   ./build.sh --setup-wine     Wine prefix .wine-build with Windows Python + PySide6 + PyInstaller (once)
#   ./build.sh [--linux|--windows]   build (default: both)
set -euo pipefail; cd "$(dirname "$0")"
PYWIN_VER=3.12.10
export WINEPREFIX="$PWD/.wine-build" WINEDEBUG=-all
WINPY='C:\Python312\python.exe'
HIDDEN="bodypak bodybones bodypak_abp bodyscale_groups weaponpak weapon_skins idlepak idle_mods pak11_extract pakio oodle_kraken uasset_props uasset_pkg uasset_datatable"

pyi_args() {   # common PyInstaller arguments; the converters are flat modules found via --paths, some imported lazily
  ARGS=(--noconfirm --onefile --windowed --name AltUIConverter --paths altui_tool/converters
        --exclude-module oodle_native --exclude-module tkinter
        --add-data "altui_tool/converters/SOURCE.txt:altui_tool/converters"
        --add-data "altui_tool/assets/icon.png:altui_tool/assets"
        --icon altui_tool/assets/icon.ico --distpath dist)
  for m in $HIDDEN; do ARGS+=(--hidden-import "$m"); done
}

setup() {
  python3 -m venv .venv
  .venv/bin/pip install -r requirements-build.txt
}

setup_wine() {   # Python from the NuGet package: the python.org installer never finishes under Wine
  mkdir -p .wine-build/cache
  local f=".wine-build/cache/python-$PYWIN_VER.nupkg"
  [ -f "$f" ] || curl -fL -o "$f" "https://www.nuget.org/api/v2/package/python/$PYWIN_VER"
  wineboot -i
  rm -rf .wine-build/cache/nupkg; mkdir -p .wine-build/cache/nupkg
  (cd .wine-build/cache/nupkg && unzip -oq "../python-$PYWIN_VER.nupkg")
  mkdir -p "$WINEPREFIX/drive_c/Python312"
  cp -r .wine-build/cache/nupkg/tools/. "$WINEPREFIX/drive_c/Python312/"
  wine "$WINPY" -m ensurepip
  wine "$WINPY" -m pip install --upgrade pip
  wine "$WINPY" -m pip install -r requirements-build.txt
}

build_linux() {
  pyi_args
  .venv/bin/pyinstaller "${ARGS[@]}" --workpath build/linux run_app.py
  mkdir -p build; dist/AltUIConverter --selftest build/selftest-linux.txt
  cat build/selftest-linux.txt
}

build_windows() {
  pyi_args
  mkdir -p build/windows
  wine "$WINPY" scripts/version_file.py build/windows/version_info.txt
  wine "$WINPY" -m PyInstaller "${ARGS[@]}" --version-file build/windows/version_info.txt \
       --workpath build/windows run_app.py
  wine dist/AltUIConverter.exe --selftest build/selftest-windows.txt
  cat build/selftest-windows.txt
}

case "${1:-}" in
  --setup) setup ;;
  --setup-wine) setup_wine ;;
  --linux) build_linux ;;
  --windows) build_windows ;;
  "") build_linux; build_windows ;;
  *) echo "usage: $0 [--setup|--setup-wine|--linux|--windows]" >&2; exit 2 ;;
esac
