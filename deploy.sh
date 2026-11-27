#!/bin/sh
# Sync the skin to the CoreELEC box and restart Kodi (for testing; releases go through GitHub -> the Kodi repo).
# Restart, not ReloadSkin(): reloading the skin while an add-on's Python is running (e.g. POV still scraping)
# crashes Kodi 22 RC.
# Usage: ./deploy.sh [skin id]   (default skin.nocturne.custom; KODI_HOST or 192.168.1.142)
set -e
HOST="${KODI_HOST:-192.168.1.142}"
SKIN="${1:-skin.nocturne.custom}"
cd "$(dirname "$0")"

# A test copy is labelled just above the published version (1.0.6 -> 1.0.6.1): Kodi's add-on updates would
# otherwise replace a "1.0.0" test copy with the published one, and the next release still replaces this.
PUB=$(curl -fsS --max-time 10 https://animate98.github.io/kodi-nocturne-custom/addons.xml 2>/dev/null \
      | grep -o "<addon id=\"$SKIN\"[^>]*version=\"[^\"]*\"" | sed 's/.*version="\([^"]*\)"/\1/')
TMP=$(mktemp -d)
rsync -a --exclude '.DS_Store' "$SKIN/" "$TMP/$SKIN/"
if [ -n "$PUB" ]; then
  sed -i.bak "s/\(<addon id=\"$SKIN\"[^>]*version=\"\)[^\"]*\"/\1$PUB.1\"/" "$TMP/$SKIN/addon.xml" && rm -f "$TMP/$SKIN/addon.xml.bak"
fi
rsync -a --delete "$TMP/$SKIN/" "root@$HOST:/storage/.kodi/addons/$SKIN/"
rm -rf "$TMP"
rsync -a "$SKIN/keymaps/" "root@$HOST:/storage/.kodi/userdata/keymaps/"
ssh -o BatchMode=yes "root@$HOST" 'systemctl restart kodi'
echo "Deployed $SKIN to $HOST and restarted Kodi."
