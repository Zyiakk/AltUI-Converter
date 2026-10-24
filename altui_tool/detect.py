"""Which kind of mod a pak is - asked of the converters themselves, so tool and converter agree."""
from dataclasses import dataclass
from altui_tool import converters  # noqa: F401  (puts the converters on sys.path)
import bodypak, bodyscale_groups, idlepak, idle_mods, weaponpak, weapon_skins
from pakio import open_pak
from altui_tool.i18n import tr

KINDS = ("body", "weapon", "idle")
# what a converted pak's folder starts with, as the converters (and AltUI's scan) name them
CONVERTED = (("body", bodyscale_groups.MOD_PREFIXES), ("weapon", weapon_skins.MOD_PREFIXES), ("idle", (idle_mods.MOD_PREFIX,)))


@dataclass
class Detection:
    kind: str                       # "body" | "weapon" | "idle" | "unknown"
    weapon: str | None = None       # weapon mods: the weapon, when the pak tells
    parts: tuple = ()               # weapon mods: of "skin", "model", "sound"
    message: str = ""               # shown under the form
    blocking: bool = False          # the converter would refuse this pak as the detected kind
    needs_game_pak: bool = False    # a shot sound that is the wave behind the game's cue: the converter needs pakchunk0


def detect(path):
    pk = None
    try:
        pk = open_pak(path)
        return _detect(pk)
    except Exception:
        return Detection("unknown", message=tr("detect.unreadable"), blocking=True)
    finally:
        if pk is not None:
            pk.f.close()      # an open handle would keep Windows from deleting or overwriting the file


def converted(paths):
    """The kind when the pak is already an AltUI mod: everything in one /Game/Mod/<prefix><name>/ folder."""
    folders = {p.split("/")[3] if p.startswith("/Game/Mod/") and p.count("/") > 3 else None for p in paths}
    if len(folders) != 1 or None in folders:
        return None
    folder = folders.pop()
    return next((kind for kind, prefixes in CONVERTED if folder.startswith(prefixes)), None)


def _detect(pk):
    paths = sorted(p for p in (bodypak.pkg_path(pk, k) for k in pk.files) if p)
    done = converted(paths)
    if done:
        return Detection(done, message=tr("detect.converted", kind=tr("kind." + done)), blocking=True)
    try:
        bodypak.find_mesh(pk)
        return Detection("body")
    except SystemExit:
        pass
    if idle_mods.GAME_IDLE.lower() in {p.lower() for p in paths}:
        try:
            idlepak.find_idle(pk)
            return Detection("idle")
        except SystemExit as e:
            return Detection("idle", message=str(e), blocking=True)
    try:
        tex, meshes, weapon, _icon, sounds, _paints = weaponpak.collect(pk, None)
    except SystemExit as e:
        weaponish = any(weaponpak.weapon_rel(pk, k) for k in pk.files) or any(weapon_skins.shot_targets(p) for p in paths)
        if not weaponish:
            return Detection("unknown", message=tr("detect.unknown", paths=", ".join(paths[:5]) or "-"))
        if str(e).startswith("cannot tell which weapon"):
            return Detection("weapon", message=tr("detect.pick_weapon"))
        return Detection("weapon", message=str(e), blocking=True)
    parts = tuple(n for n, on in (("skin", tex), ("model", meshes), ("sound", sounds)) if on)
    return Detection("weapon", weapon=weapon, parts=parts, needs_game_pak="wave" in sounds.values())
