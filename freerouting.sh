#!/usr/bin/env bash
# Run the prebuilt freerouting jar headless with the bundled minimal JRE.
# Usage: ./freerouting.sh -de in.dsn -do out.ses [-mp passes] ...
set -e
D="$(cd "$(dirname "$0")" && pwd)"
if [ ! -x "$D/linux-x64/rt/bin/java" ]; then
  tar -C "$D/linux-x64" -xJf "$D/linux-x64/jre25-freerouting-linux-x64.tar.xz"
fi
exec "$D/linux-x64/rt/bin/java" -Djava.awt.headless=true -jar "$D/freerouting.jar" --gui.enabled=false "$@"
