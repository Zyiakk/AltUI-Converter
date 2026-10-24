"""Mod name and title from a pak's file name."""
import re

PREFIXES = {"body": "BodyAltUI_", "weapon": "WeaponAltUI_", "idle": "IdleAltUI_"}
_KNOWN_PREFIXES = ("BodyAltUI_", "Body_", "WeaponAltUI_", "IdleAltUI_")
_NEXUS = re.compile(r"-\d+(?:-\d+)*-\d{9,}$")                              # Nexus download: -<mod id>-<version>-<unix time>
_VERSION = re.compile(r"[ _-](?:v\d+(?:\.\d+)*|\d+(?:\.\d+)+)$", re.I)    # _v1, _v1.2, -0.6, " 1.2.3"
_PAK_P = re.compile(r"_p$", re.I)                                         # UE patch-pak suffix


def base_name(filename):
    """The editable part of the mod name: file name without .pak, Nexus suffix, version, _P and mod prefix."""
    s = filename[:-4] if filename.lower().endswith(".pak") else filename
    while True:
        t = _PAK_P.sub("", _VERSION.sub("", _NEXUS.sub("", s)))
        if t == s:
            break
        s = t
    for p in _KNOWN_PREFIXES:
        if s.lower().startswith(p.lower()):
            s = s[len(p):]
            break
    s = re.sub(r"_+", "_", re.sub(r"[^A-Za-z0-9_]", "_", s)).strip("_")
    return s or "Mod"


def title_of(name):
    return name.replace("_", " ").strip() or name


def valid(name):
    return re.fullmatch(r"[A-Za-z0-9_]+", name) is not None
