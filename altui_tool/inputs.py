"""What was dropped -> exactly one .pak on disk."""
import os, shutil, zipfile
from altui_tool.i18n import tr


class InputError(Exception):
    pass


def resolve(path, choose, tmp_dir):
    """The .pak itself, or the one .pak of a .zip extracted into tmp_dir. With several paks in the zip, choose(member names)
    picks one (None = cancelled -> None)."""
    low = path.lower()
    if low.endswith(".pak"):
        return path
    if not low.endswith(".zip"):
        raise InputError(tr("input.bad_type"))
    try:
        with zipfile.ZipFile(path) as zf:
            names = [n for n in zf.namelist() if n.lower().endswith(".pak") and not n.endswith("/")]
            if not names:
                raise InputError(tr("input.no_pak"))
            name = names[0] if len(names) == 1 else choose(names)
            if name is None:
                return None
            out = os.path.join(tmp_dir, os.path.basename(name))     # basename: no path from the archive reaches the disk
            with zf.open(name) as src, open(out, "wb") as dst:
                shutil.copyfileobj(src, dst)
            return out
    except zipfile.BadZipFile:
        raise InputError(tr("input.bad_zip"))
