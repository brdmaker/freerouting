#!/usr/bin/env python3
"""Headless KiCad <-> Specctra helper using KiCad's pcbnew Python API.

  kicad_dsn.py export <board.kicad_pcb> <out.dsn>
  kicad_dsn.py import <board.kicad_pcb> <in.ses> <out.kicad_pcb>

Run with the Python that ships with KiCad (it provides `pcbnew`).
NOTE: written from the API calls the freerouting KiCad plugin uses; not tested in the
container where this file was committed (no KiCad there). Test on your board first.
"""
import sys

try:
    import pcbnew
except ImportError:
    sys.exit("pcbnew not found: run with KiCad's own Python (e.g. KiCad's bundled python3).")


def main(argv):
    if len(argv) < 4 or argv[1] not in ("export", "import"):
        sys.exit(__doc__)
    board = pcbnew.LoadBoard(argv[2])
    if argv[1] == "export":
        ok = pcbnew.ExportSpecctraDSN(board, argv[3])
        sys.exit(0 if ok else "ExportSpecctraDSN failed")
    if len(argv) != 5:
        sys.exit(__doc__)
    ok = pcbnew.ImportSpecctraSES(board, argv[3])
    if not ok:
        sys.exit("ImportSpecctraSES failed")
    pcbnew.SaveBoard(argv[4], board)


if __name__ == "__main__":
    main(sys.argv)
