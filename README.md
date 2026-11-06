# freerouting binaries (orphan branch)

Prebuilt headless-capable freerouting, built from `master` @ `099368c6` (v2.5.1-SNAPSHOT, 2026-11-06).

| File | What |
|---|---|
| `freerouting.jar` | fat jar (`./gradlew executableJar -x test`), needs Java 25 |
| `linux-x64/jre25-freerouting-linux-x64.tar.xz` | minimal JRE 25 (jlink, ~60 MB unpacked) from Oracle JDK 25.0.5; unpacks to `rt/` |
| `freerouting.sh` | unpacks the JRE on first use and runs the jar headless |

Use: `./freerouting.sh -de board.dsn -do board.ses -mp 20`

JRE modules: java.base, desktop, logging, naming, net.http, sql, xml, management, prefs, scripting,
security.jgss, compiler, jdk.unsupported, jdk.crypto.ec, jdk.management, jdk.jfr.

Verified: routed `fixtures/Issue027-zMRETestFixture.dsn` (251 nets -> 5 unrouted after 2 passes) and
`tutorial_board.dsn` with this JRE. Rebuild: JDK 25 + `./gradlew executableJar -x test`.
Note: the jar tries analytics calls on start; they fail harmlessly when the network blocks them.

## Render a routed board

`python3 -I render_board.py board.dsn board.ses out.png` (needs Pillow) draws F.Cu and mirrored B.Cu
side by side. Quick visual check only; run the design rules check in your EDA tool.
