"""Synthetic mod paks for the tests and --selftest: tiny, but real enough for the converters
(cooked package headers via uasset_pkg, pak v11 via bodypak.write_pak)."""
import os, struct
from altui_tool import converters  # noqa: F401  (puts the converters on sys.path)
import bodypak, idle_mods
from uasset_pkg import Package, Export

MOUNT = "../../../TheKillingAntidote/Content/"
SKEL = "/Game/Project/Character/Jodi/Body/Female_Skeleton"
JODI_ANIM = "/Game/Project/Character/Jodi/Jodi_Anim"


def package(obj, cls, refs=()):
    """A cooked package: one export <obj> of class <cls> with an empty tagged-property list, one import per
    (package path, class, object name) in refs. Returns (uasset, uexp)."""
    pkg = Package(); pkg.guid = b"\0" * 16
    data = struct.pack("<ii", pkg.name_index("None"), 0) + b"\0" * 4
    eng = pkg.add_import("/Script/CoreUObject", "Package", 0, "/Script/Engine")
    for path, icls, o in refs:
        p = pkg.add_import("/Script/CoreUObject", "Package", 0, path)
        pkg.add_import("/Script/Engine", icls, p, o)
    c = pkg.add_import("/Script/CoreUObject", "Class", eng, cls)
    cdo = pkg.add_import("/Script/Engine", cls, eng, "Default__" + cls)
    pkg.exports.append(Export(c, 0, cdo, 0, obj, 0, 0xb, data))
    pkg.depends = [[] for _ in pkg.exports]; pkg.generations = [(len(pkg.exports), 0)]
    return pkg.write()


def _entries(rel, ua_ux):
    ua, ux = ua_ux
    return [(rel + ".uasset",) + bodypak.plain_entry(ua), (rel + ".uexp",) + bodypak.plain_entry(ux)]


def _raw(rel, payload):
    """A package whose bytes the converter only copies (textures)."""
    return [(rel + ".uasset",) + bodypak.plain_entry(b"UASSET" + payload), (rel + ".uexp",) + bodypak.plain_entry(b"UEXP")]


def _write(path, mount, entries, seed):
    bodypak.write_pak(path, mount, [], entries, seed)
    return path


def body_pak(path):
    return _write(path, MOUNT, _entries("Project/Character/Jodi/Body/Female",
                                        package("Female", "SkeletalMesh", [(SKEL, "Skeleton", "Female_Skeleton")])), 1)


def idle_pak(path):
    e = _entries("Project/Character/Jodi/Animations/Female_Idle", package("Female_Idle", "AnimSequence"))
    e += _entries("Project/Something/Else", package("Else", "Texture2D"))
    return _write(path, MOUNT, e, 2)


def idle_dep_pak(path):
    """An idle replacer whose animation imports another package of the same pak - idlepak refuses that."""
    curve = "/Game/Project/Character/Jodi/Animations/Idle_Curve"
    e = _entries("Project/Character/Jodi/Animations/Female_Idle",
                 package("Female_Idle", "AnimSequence", [(curve, "CurveFloat", "Idle_Curve")]))
    e += _entries("Project/Character/Jodi/Animations/Idle_Curve", package("Idle_Curve", "CurveFloat"))
    return _write(path, MOUNT, e, 3)


def altui_pak(path):
    """An AltUI.pak with two idle templates (what idlepak copies from the installed AltUI)."""
    e = []
    for walk, run in (("Normal", "Normal"), ("Catwalk", "Normal")):
        n = idle_mods.template_name(walk, run)
        e += _entries("Mod/AltUI/" + n, package(n + "_C", "AnimBlueprintGeneratedClass", [
            (JODI_ANIM, "AnimBlueprintGeneratedClass", "Jodi_Anim_C"),
            (idle_mods.TEMPLATE_ANIM, "AnimSequence", "Female_IdleTemplate")]))
    return _write(path, MOUNT, e, 4)


def weapon_skin_pak(path):
    e = []
    for rel in ("models/weapon/UMP45/Material/T_UMP45_BaseColor", "models/weapon/UMP45/Material/T_UMP45_Normal"):
        e += _raw(rel, rel.encode())
    return _write(path, MOUNT + "Project/", e, 5)


def weapon_normal_only_pak(path):
    return _write(path, MOUNT + "Project/", _raw("models/weapon/UMP45/Material/T_UMP45_Normal", b"N"), 6)


def weapon_unknown_pak(path):
    """A melee model in a folder that names no weapon - the user has to pick it."""
    return _write(path, MOUNT + "Project/", _entries("models/weapon/Meelee/SM_Knife", package("SM_Knife", "StaticMesh")), 7)


def other_pak(path):
    return _write(path, MOUNT, _entries("Project/Something/Else", package("Else", "Texture2D")), 8)


def game_tree(steam_root):
    """A Steam library with the game: <root>/steamapps/common/TheKillingAntidote/TheKillingAntidote/{Mods,Content/Paks}."""
    game = os.path.join(steam_root, "steamapps", "common", "TheKillingAntidote")
    inner = os.path.join(game, "TheKillingAntidote")
    os.makedirs(os.path.join(inner, "Mods"), exist_ok=True)
    os.makedirs(os.path.join(inner, "Content", "Paks"), exist_ok=True)
    altui_pak(os.path.join(inner, "Mods", "AltUI.pak"))
    open(os.path.join(inner, "Content", "Paks", "pakchunk0-WindowsNoEditor.pak"), "wb").close()
    return game
