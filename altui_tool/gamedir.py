"""Where the game is (Steam libraries on Windows and Linux) and the paths the converters need from it."""
import glob, os, re, sys
from dataclasses import dataclass

APP_DIR = "TheKillingAntidote"        # steamapps/common/<APP_DIR>/<APP_DIR>/{Mods, Content/Paks}


@dataclass
class GamePaths:
    root: str | None = None           # …/steamapps/common/TheKillingAntidote
    mods: str | None = None           # <root>/TheKillingAntidote/Mods - where converted mods go
    altui_pak: str | None = None      # <mods>/AltUI.pak, when installed (idle templates)
    pakchunk0: str | None = None      # <root>/TheKillingAntidote/Content/Paks/pakchunk0-*.pak (weapon sound cue)


def steam_roots():
    roots = []
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as k:
                roots.append(winreg.QueryValueEx(k, "SteamPath")[0])
        except OSError:
            pass
        roots.append(os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "Steam"))
    else:
        home = os.path.expanduser("~")
        roots += [os.path.join(home, ".local", "share", "Steam"), os.path.join(home, ".steam", "steam"),
                  os.path.join(home, ".var", "app", "com.valvesoftware.Steam", ".local", "share", "Steam")]
    return roots


def library_folders(root):
    """The Steam root itself and every library in its steamapps/libraryfolders.vdf."""
    out = [root]
    try:
        with open(os.path.join(root, "steamapps", "libraryfolders.vdf"), encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return out
    out += [m.group(1).replace("\\\\", "\\") for m in re.finditer(r'"path"\s+"((?:[^"\\]|\\.)*)"', text)]
    return out


def normalize(path):
    """The game root for a folder the user picked - the root itself or its inner TheKillingAntidote folder; else None."""
    if not path:
        return None
    path = os.path.abspath(path)
    for cand in (path, os.path.dirname(path)):
        inner = os.path.join(cand, APP_DIR)
        if os.path.isdir(os.path.join(inner, "Content")) or os.path.isdir(os.path.join(inner, "Mods")):
            return cand
    return None


def find_game(roots=None):
    seen = set()
    for root in (steam_roots() if roots is None else roots):
        for lib in library_folders(root):
            key = os.path.normcase(os.path.realpath(lib))
            if key in seen:
                continue
            seen.add(key)
            game = normalize(os.path.join(lib, "steamapps", "common", APP_DIR))
            if game:
                return game
    return None


def paths(root):
    if not root:
        return GamePaths()
    inner = os.path.join(root, APP_DIR)
    mods = os.path.join(inner, "Mods")
    altui = os.path.join(mods, "AltUI.pak")
    chunks = sorted(glob.glob(os.path.join(glob.escape(inner), "Content", "Paks", "pakchunk0-*.pak")))
    return GamePaths(root, mods, altui if os.path.isfile(altui) else None, chunks[0] if chunks else None)
