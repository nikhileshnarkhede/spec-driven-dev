#!/usr/bin/env bash
# Install the dev-workflow commands, agents and hook into your Claude Code config.
# Existing files with the same name are backed up, never silently overwritten.
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
STAMP="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$DEST/skills" "$DEST/agents" "$DEST/hooks" "$DEST/scripts"

install_item() {  # $1 = source path, $2 = destination path
  if [ -e "$2" ]; then
    mv "$2" "$2.bak-$STAMP"
    echo "backed up  $2 -> $2.bak-$STAMP"
  fi
  cp -r "$1" "$2"
  echo "installed  $2"
}

for d in "$SRC"/skills/*/; do
  name="$(basename "$d")"
  install_item "$SRC/skills/$name" "$DEST/skills/$name"
done
for f in "$SRC"/agents/*.md; do
  install_item "$f" "$DEST/agents/$(basename "$f")"
done
for f in "$SRC"/hooks/*.py; do
  install_item "$f" "$DEST/hooks/$(basename "$f")"
done
for f in "$SRC"/scripts/*.py; do
  install_item "$f" "$DEST/scripts/$(basename "$f")"
done

cat <<EOF

Done. One manual step: merge the Stop hook from settings.example.json into
$DEST/settings.json (don't replace the file; add the "hooks" block).
Then restart Claude Code and type /dev- to see the commands.
EOF
