# freerouting binaries (orphan branch)

Prebuilt headless-capable freerouting, built from `master` @ `01db81ca` (v2.5.1-SNAPSHOT, 2026-11-15).

| File | What |
|---|---|
| `freerouting.jar` | fat jar (`./gradlew executableJar -x test`), needs Java 25 |
| `linux-x64/jre25-freerouting-linux-x64.tar.xz` | minimal JRE 25 (jlink, ~60 MB unpacked) from Oracle JDK 25.0.5; unpacks to `rt/` |
| `skills/freerouting/` | Claude skill: KiCad workflow (`SKILL.md`) + tuning guide (`tuning.md`); copy the folder to `.claude/skills/` |
| `kicad_dsn.py` | KiCad pcbnew DSN export / SES import helper (untested) |
| `freerouting.sh` | unpacks the JRE on first use and runs the jar headless |

Use: `./freerouting.sh -de board.dsn -do board.ses -mp 20`

JRE modules: java.base, desktop, logging, naming, net.http, sql, xml, management, prefs, scripting,
security.jgss, compiler, jdk.unsupported, jdk.crypto.ec, jdk.management, jdk.jfr.

Verified: routed an 2-layer 120-net board (ar488) with this JRE: 0 unrouted, no violations, ~2 min.
Note: the jar tries analytics calls on start; they fail harmlessly when the network blocks them.

## Render a routed board

`python3 -I render_board.py board.dsn board.ses out.png` (needs Pillow) draws F.Cu and mirrored B.Cu
side by side. Quick visual check only; run the design rules check in your EDA tool.
