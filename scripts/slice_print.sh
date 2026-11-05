#!/usr/bin/env bash
# Reproducible slicing of a TiaCAD model with PrusaSlicer (CLI).
#
#   scripts/slice_print.sh extract <known-good.gcode> <base.ini>
#       Pull the slicer config embedded in a G-code file into a base .ini.
#
#   scripts/slice_print.sh slice <printing-dir> <profile>
#       Build the model STL, slice it with <printing-dir>/profiles/<profile>.conf,
#       verify the G-code header, and append a row to <printing-dir>/slice_log.tsv.
#       Output: <printing-dir>/out/<GCODE_NAME>.gcode (gitignored).
#
# A profile is a bash file that sets:
#   BASE         base .ini, relative to the printing dir
#   MODEL        TiaCAD YAML, relative to the printing dir
#   SETS         tiacad --set overrides (string, may be empty)
#   GCODE_NAME   output name without extension
#   ARGS         PrusaSlicer CLI overrides on top of BASE
#   NOTE         one line: what this variant tests / changed vs its parent
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APPIMAGE="${PRUSASLICER:-$HOME/bin/PrusaSlicer-2.9.6-x86_64_GN.AppImage}"

die() { echo "slice_print: $*" >&2; exit 1; }

hdr() { grep -m1 "^; $2 = " "$1" | sed "s/^; $2 = //"; }

cmd="${1:-}"; shift || true
case "$cmd" in
extract)
    [ $# -eq 2 ] || die "usage: extract <gcode> <out.ini>"
    gcode="$1"; out="$2"
    [ -f "$gcode" ] || die "no such file: $gcode"
    grep -q '^; prusaslicer_config = begin' "$gcode" || die "no embedded config in $gcode"
    mkdir -p "$(dirname "$out")"
    sed -n '/^; prusaslicer_config = begin/,/^; prusaslicer_config = end/p' "$gcode" \
        | sed '1d;$d' | sed 's/^; //' > "$out"
    echo "extracted $(wc -l < "$out") settings -> $out"
    ;;
slice)
    [ $# -eq 2 ] || die "usage: slice <printing-dir> <profile>"
    pdir="$(cd "$1" && pwd)"; profile="$2"
    conf="$pdir/profiles/$profile.conf"
    [ -f "$conf" ] || die "no profile: $conf"
    [ -x "$APPIMAGE" ] || die "PrusaSlicer AppImage not found: $APPIMAGE (set PRUSASLICER)"
    SETS=""; ARGS=""; NOTE=""
    # shellcheck disable=SC1090
    source "$conf"
    base="$pdir/$BASE"; model="$pdir/$MODEL"
    [ -f "$base" ] || die "missing base config $base (run: extract <good.gcode> $base)"
    mkdir -p "$pdir/out"
    stl="$pdir/out/$(basename "${MODEL%.yaml}").stl"
    out="$pdir/out/$GCODE_NAME.gcode"

    set_flags=(); for s in $SETS; do set_flags+=(--set "$s"); done
    (cd "$REPO" && ./tiacad build "$model" -o "$stl" "${set_flags[@]}")

    # AppImage ignores relative paths: everything below is absolute.
    # shellcheck disable=SC2086
    "$APPIMAGE" -g --load "$base" $ARGS --output "$out" "$stl"

    echo "--- header check: $out"
    for k in printer_settings_id nozzle_diameter layer_height perimeters bottom_solid_layers \
             top_solid_layers temperature first_layer_temperature max_fan_speed min_fan_speed \
             filament_max_volumetric_speed; do
        printf '%-32s %s\n' "$k" "$(hdr "$out" "$k")"
    done
    t="$(grep -m1 '^; estimated printing time (normal mode)' "$out" | sed 's/.*= //')"
    g="$(hdr "$out" 'total filament used \[g\]')"
    layers="$(grep -c '^;LAYER_CHANGE' "$out" || true)"
    bounds="$(awk '/^G[01] /{for(i=2;i<=NF;i++){c=substr($i,1,1);v=substr($i,2)+0;
        if(c=="X"){if(xmin==""||v<xmin)xmin=v;if(v>xmax)xmax=v}
        if(c=="Y"){if(ymin==""||v<ymin)ymin=v;if(v>ymax)ymax=v}
        if(c=="Z"&&v>zmax)zmax=v}}
        END{printf "X %.1f..%.1f  Y %.1f..%.1f  Zmax %.1f",xmin,xmax,ymin,ymax,zmax}' "$out")"
    echo "time $t | filament ${g}g | layers $layers | $bounds"
    log="$pdir/slice_log.tsv"
    [ -f "$log" ] || printf 'date\tprofile\tgcode\test_time\tgrams\tlayers\tmodel_commit\tnote\n' > "$log"
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$(date +%F)" "$profile" "$GCODE_NAME.gcode" \
        "$t" "$g" "$layers" "$(git -C "$REPO" rev-parse --short HEAD)" "$NOTE" >> "$log"
    echo "logged -> $log"
    ;;
*) sed -n '2,22p' "${BASH_SOURCE[0]}"; exit 2 ;;
esac
