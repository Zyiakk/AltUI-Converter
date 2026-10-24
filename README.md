# AltUI Mod Converter

Body, weapon and idle-animation mods for **The Killing Antidote** replace the game's own files, so only one of each can
be active, and AltUI cannot offer them as a choice. This tool turns such a mod into an AltUI mod: it then shows up in
AltUI next to the game's own options (Body Shape tab, Weapons tab, Options › Move › Standing) and can be switched at
any time. It does what `bodypak.pyz`, `weaponpak.pyz` and `idlepak.pyz` do, with a window instead of a command line,
and needs nothing else installed.

## Use

1. Start `AltUIConverter.exe` (Windows) or `AltUIConverter` (Linux).
2. Check the game folder at the top. It is found through Steam; if not, pick
   `…/steamapps/common/TheKillingAntidote` with **Browse…**.
3. Drag the mod's `.pak` – or the `.zip` you downloaded – onto the drop area, or click it to pick the file.
4. The type (body, weapon, idle animation) is detected and a name is filled in. Change name and title if you like;
   the title is what AltUI shows.
5. Click **Convert**. The converted mod goes straight into the game's `TheKillingAntidote/Mods` folder.

### Options

| Type | Option | What it does |
|---|---|---|
| Body | Keep the mod's own animation blueprint | For bodies whose shape comes from their own blueprint and that should work without AltUI. The Body Shape sliders then have no effect on this body. |
| Weapon | Weapon | Needed when the pak does not tell which weapon it is for (melee weapons). |
| Idle | AltUI.pak | Idle mods are built from templates inside AltUI; the installed `Mods/AltUI.pak` is used. |
| All | Overwrite existing | Replace an earlier conversion with the same name without asking. |

When a conversion fails, the log says why. **Copy details** copies the message for a bug report.

## Build from source

Linux with Python 3, Wine, curl and unzip:

    ./build.sh --setup          # once: .venv with PySide6 and PyInstaller
    ./build.sh --setup-wine     # once: Windows Python in a Wine prefix
    ./build.sh                  # dist/AltUIConverter and dist/AltUIConverter.exe, each self-tested

Tests: `.venv/bin/python -m unittest discover -s tests -t . -v`

The converters in `altui_tool/converters` are those of an AltUI release, taken from a checkout of the AltUI repository
next to this one with `scripts/sync_converters.sh [<tag>]` (default: the newest release); they are not edited here.
About shows which AltUI version they belong to.

## License

GPL-3.0 (see LICENSE). The Oodle decoder is a Python port of ooz (GPL-3.0). Qt for Python (PySide6) is LGPL-3.0.
