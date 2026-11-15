---
name: freerouting
description: Use when you need to autoroute a KiCad PCB headless with the prebuilt freerouting from the `binaries` branch of brdmaker/freerouting (get the binary, export DSN, route, import SES, check with kicad-cli DRC, render a PNG), or to tune routing results (via-to-pad spacing, vias, passes, optimizer, priority nets, planes).
---

# freerouting headless with KiCad

Prebuilt freerouting lives on the orphan branch `binaries` of `brdmaker/freerouting`
(`freerouting.jar`, a minimal Java 25 runtime, `freerouting.sh`, `render_board.py`, `kicad_dsn.py`).
Tuning recipes: `tuning.md` next to this file.

## 1. Get the binary

```bash
git clone --branch binaries --depth 1 https://github.com/brdmaker/freerouting.git /tmp/fr-bin
/tmp/fr-bin/freerouting.sh -help      # first run unpacks the bundled JRE (linux-x64 only)
```

`freerouting.sh` runs `java -Djava.awt.headless=true -jar freerouting.jar --gui.enabled=false "$@"`.
On other platforms use any Java 25: `java -jar freerouting.jar --gui.enabled=false ...`.
The jar logs a harmless warning when its analytics call is blocked; add `-da` to disable analytics.

## 2. KiCad -> DSN

KiCad's Python module is the supported way (the freerouting KiCad plugin does the same):

```bash
python3 /tmp/fr-bin/kicad_dsn.py export board.kicad_pcb board.dsn    # needs KiCad's python (pcbnew)
```

If your `kicad-cli` has a Specctra export (`kicad-cli pcb export --help`, newer versions), that works too.
Before exporting: remove old tracks/vias you want rerouted; fix net names with odd characters (Ω, µ, Φ).

## 3. Route

```bash
/tmp/fr-bin/freerouting.sh -de board.dsn[+board.kicad_dru][+board.kicad_pro] -do board.ses \
    --router.autorouter.max_passes=30 -da
```

- `-de a.dsn+a.kicad_dru+a.kicad_pro`: the `.kicad_dru` (custom clearance rules) and `.kicad_pro`
  (min track width -> `--router.neck_width_um`) are **not** read unless given explicitly. KiCad does
  not write either into the DSN, so always pass them when the board has custom rules.
- Output format follows the extension: `.ses` (KiCad), `.dsn`, `.scr` (Fusion).
- `-drc report.json` writes freerouting's own DRC in KiCad JSON schema.
- `--router.optimizer.enabled=false` skips optimization (fast first look).
- Read the log: "Auto-routing stage completed ... (N unrouted and V violations)" must be 0 and 0.
  A run that ends with unrouted nets still writes a .ses: do not import blindly.

## 4. SES -> KiCad, check

```bash
python3 /tmp/fr-bin/kicad_dsn.py import board.kicad_pcb board.ses board_routed.kicad_pcb
kicad-cli pcb drc --severity-all --format json -o drc.json board_routed.kicad_pcb
python3 -I /tmp/fr-bin/render_board.py board.dsn board.ses routed.png   # quick look, needs Pillow
```

KiCad's DRC is the authority, not freerouting's score and not the PNG. Look at `routed.png` yourself.

## 5. Tune

See `tuning.md`. Change one thing per run, compare unrouted/violations, via count, run time.

## Limits (honest)

- Verified here: the jar + bundled JRE routing a KiCad 10 DSN (2-layer, 120 nets, 0 unrouted, no
  violations) and the DSN `smd_via` clearance rule. NOT verified here: `kicad_dsn.py` (no KiCad in the
  build container), `kicad-cli pcb drc` flags, KiCad import of the SES, the `.kicad_dru` /
  `.kicad_pro` options of the new master. Test them once on your board before relying on them.
