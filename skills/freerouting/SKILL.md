---
name: freerouting
description: Use when you need to autoroute a KiCad PCB headless with the prebuilt freerouting from the `binaries` branch of brdmaker/freerouting (get the binary, export DSN, route, import SES, check with kicad-cli DRC, render a PNG), or to tune routing results (via-to-pad spacing, vias, passes, optimizer, priority nets, planes).
---

# freerouting headless with KiCad

Prebuilt freerouting lives on the orphan branch `binaries` of `brdmaker/freerouting`
(`freerouting.jar`, a minimal Java 25 runtime, `freerouting.sh`, `render_board.py`, `kicad_dsn.py`).
Tuning recipes: `tuning.md` next to this file.

## 1. Get the binary

Preferred (hash-pinned, installs a launcher): the `kicad-setup` skill of `brdmaker/kicad`
(branch `claude-skills`): `~/.claude/skills/kicad-setup/scripts/setup.sh freerouting`, which gives
`~/.cache/freerouting-skill/bin/freerouting` (use it wherever this skill says `freerouting.sh`).

Manual:

```bash
git clone --branch binaries --depth 1 https://github.com/brdmaker/freerouting.git /tmp/fr-bin
/tmp/fr-bin/freerouting.sh -help      # first run unpacks the bundled JRE (linux-x64 only)
```

Both run `java -Djava.awt.headless=true -jar freerouting.jar --gui.enabled=false "$@"` with the bundled
JRE 25 (system Java 21 cannot run the jar). On other platforms use any Java 25.
The jar logs a harmless warning when its analytics call is blocked; add `-da` to disable analytics.

## 2. KiCad -> DSN

With the `kicad-cli` skill (bundled KiCad 10 `kicad-cli`):

```bash
kicad-cli pcb export specctra -o board.dsn board.kicad_pcb
```

Before exporting: remove old tracks/vias you want rerouted; avoid characters like Ω, µ, Φ in net names.
(Without that skill any KiCad 10 `kicad-cli` works; older KiCad: `pcbnew.ExportSpecctraDSN(board, path)`.)

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

Importing the SES is the one step `kicad-cli` cannot do, and the bundled KiCad 10 build has no Python
`pcbnew`. Options: KiCad GUI (PCB Editor: File > Import > Specctra Session), or a KiCad install whose
Python has `pcbnew`:

```bash
python3 kicad_dsn.py import board.kicad_pcb board.ses board_routed.kicad_pcb    # kicad_dsn.py is untested
```

Then check with the `kicad-drc` skill (`kicad-cli pcb drc`), and render a quick look from the files
you already have (needs Pillow):

```bash
python3 -I render_board.py board.dsn board.ses routed.png
```

KiCad's DRC is the authority, not freerouting's score and not the PNG. Look at `routed.png` yourself.

## 5. Tune

See `tuning.md`. Change one thing per run, compare unrouted/violations, via count, run time.

## Limits (honest)

- Verified: the jar + bundled JRE routing a KiCad 10 DSN (2-layer, 120 nets, 0 unrouted, no
  violations) and the DSN `smd_via` clearance rule. Facts about `kicad-cli pcb export specctra` and the
  missing SES import / `pcbnew` come from the `kicad` fork's `kicad-cli` skill and its source.
- NOT verified: `kicad_dsn.py`, KiCad importing the SES, and the `.kicad_dru` / `.kicad_pro` options of the
  new master. Test them once on your board before relying on them.
