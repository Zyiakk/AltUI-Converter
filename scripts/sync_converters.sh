#!/bin/bash
# Copies the converters into altui_tool/converters (unchanged), shows what changed, records the origin in SOURCE.txt.
#   scripts/sync_converters.sh [<tag>]        release: scripts/ of an AltUI release tag (default: the newest vX.Y.Z)
# Repo: ALTUI (default ../AltUI, a checkout of the AltUI repository).
set -euo pipefail; cd "$(dirname "$0")/.."
ALTUI="${ALTUI:-../AltUI}"; DST=altui_tool/converters
FILES="bodypak.py bodybones.py bodypak_abp.py bodyscale_groups.py weaponpak.py weapon_skins.py idlepak.py idle_mods.py pak11_extract.py pakio.py oodle_kraken.py uasset_props.py uasset_pkg.py uasset_datatable.py"
git -C "$ALTUI" rev-parse --git-dir >/dev/null 2>&1 || { echo "no AltUI repo at $ALTUI" >&2; exit 1; }
latest=$(git -C "$ALTUI" tag --list 'v[0-9]*' --sort=-version:refname | head -1)
[ -n "$latest" ] || { echo "no release tag in $ALTUI" >&2; exit 1; }
mkdir -p "$DST"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT

tag="${1:-$latest}"
git -C "$ALTUI" rev-parse -q --verify "refs/tags/$tag" >/dev/null || { echo "no tag $tag in $ALTUI" >&2; exit 1; }
for f in $FILES; do
  git -C "$ALTUI" show "$tag:scripts/$f" > "$tmp/$f" 2>/dev/null || { echo "$tag has no scripts/$f" >&2; exit 1; }
done
origin="AltUI ${tag#v}"

for f in $FILES; do
  if [ -f "$DST/$f" ]; then diff -u "$DST/$f" "$tmp/$f" || true; else echo "new: $f"; fi
  cp "$tmp/$f" "$DST/$f"
done
{ echo "$origin"; echo "synced $(date +%F)"; echo "files: $FILES"; } > "$DST/SOURCE.txt"
cat "$DST/SOURCE.txt"
