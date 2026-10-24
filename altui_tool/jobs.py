"""One conversion: the form's values -> the matching converter -> a result the window can show. Qt-free."""
import os, traceback
from dataclasses import dataclass, field
from altui_tool import converters  # noqa: F401  (puts the converters on sys.path)
import bodypak, idlepak, weaponpak
from altui_tool import naming
from altui_tool.i18n import tr


@dataclass
class Job:
    kind: str                       # "body" | "weapon" | "idle"
    src: str                        # the .pak to convert
    name: str                       # without prefix (naming.PREFIXES adds it)
    title: str
    out_dir: str
    force: bool = False
    keep_abp: bool = False          # body: --keep-abp
    weapon: str | None = None       # weapon: --weapon (None = from the pak)
    game_pak: str | None = None     # weapon: --game (pakchunk0)
    altui_pak: str | None = None    # idle: --altui
    dropped: str | None = None      # the file the user dropped, when it is not src itself (a .zip src came out of)


@dataclass
class Result:
    ok: bool
    summary: str
    details: list = field(default_factory=list)
    pak: str | None = None


def mod_name(job):
    return naming.PREFIXES[job.kind] + job.name


def target_path(job):
    return os.path.join(job.out_dir, mod_name(job) + ".pak")


def source_name(job):
    """The source as the log names it: the pak, and the zip it came out of."""
    pak = os.path.basename(job.src)
    return pak if not job.dropped else "%s (%s)" % (pak, os.path.basename(job.dropped))


def source_path(job):
    return job.src if not job.dropped else "%s › %s" % (job.dropped, os.path.basename(job.src))


def run(job):
    """The converter's log dict; raises SystemExit with the converter's message when it refuses."""
    if job.kind == "body":
        return bodypak.convert(job.src, mod_name(job), job.title, job.out_dir, job.force, job.keep_abp)[1]
    if job.kind == "weapon":
        return weaponpak.convert(job.src, job.name, job.title, job.out_dir, job.force, job.weapon, job.game_pak)
    if job.kind == "idle":
        if not job.altui_pak:       # never let idlepak guess an install place: the window's game folder is the one
            raise SystemExit(tr("hint.no_altui"))
        return idlepak.convert(job.src, job.name, job.title, job.out_dir, job.force, job.altui_pak)
    raise SystemExit("unknown mod type: %s" % job.kind)


def execute(job):
    """Every line names the source and, when it fails, the type it was converted as; full paths go in the details
    (they get cut off in the line)."""
    source = ["source: " + source_path(job)]
    failed = lambda error: tr("log.failed", source=source_name(job), kind=tr("kind." + job.kind), error=error)
    try:
        log = run(job)
    except SystemExit as e:
        return Result(False, failed(str(e) or "failed"), source)
    except Exception:
        return Result(False, failed(tr("log.internal")), source + traceback.format_exc().strip().splitlines())
    pak = log["pak"]
    return Result(True, tr("log.ok", source=source_name(job), pak=os.path.basename(pak), size=human_size(log["size"])),
                  source + ["folder: " + os.path.dirname(pak)] + details(job.kind, log), pak)


def details(kind, log):
    """The lines the command-line tools print after a conversion."""
    out = []
    if kind == "body":
        if log["abp"] == "AltUI":
            custom = ", ".join("%s=%s" % (k, "/".join("%.2f" % x for x in v))
                               for k, v in log["scale_defaults"].items() if v != [1.0, 1.0, 1.0])
            out.append("post-process blueprint: AltUI ABP_BodyScale (Body Shape sliders); defaults: " + (custom or "all 1.0"))
        else:
            out.append("post-process blueprint: the mod's own (no Body Shape sliders)")
        if log.get("bones_added"):
            out.append("bones of the game's mesh added: " + ", ".join(log["bones_added"]))
        out += ["warning: " + w for w in log["warnings"]]
        out += ["companion asset used by the mesh: %s -> %s" % kv for kv in sorted(log["companions"].items())]
        if log["dropped"]:
            out.append("not used by the mesh, left out: " + ", ".join(log["dropped"]))
    elif kind == "weapon":
        out.append("weapon: " + log["weapon"])
        skin = sorted(v for k, v in log["textures"].items() if k != "Icon")   # the item icon comes with skins and models
        if "Icon" in log["textures"]:
            out.append("item icon: " + log["textures"]["Icon"])
        if skin:
            out.append("skin textures: " + ", ".join(skin))
        if log["meshes"]:
            out.append("meshes: " + ", ".join(log["meshes"]))
        if log["paints"]:
            out.append("paints of the model: " + ", ".join(log["paints"]))
        if log["sound"]:
            out.append("sound: " + log["sound"])
        out += ["skipped: " + k for k in log["dropped"]]
    elif kind == "idle":
        out.append("templates: " + ", ".join(log["templates"]))
        out += ["skipped: " + k for k in log["dropped"]]
    return out


def human_size(n):
    if n < 1024:
        return "%d B" % n
    for unit in ("KB", "MB", "GB"):
        n /= 1024
        if n < 1024 or unit == "GB":
            return "%.1f %s" % (n, unit)
