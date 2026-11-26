#!/bin/sh
# Sync the skin to the CoreELEC box and restart Kodi (for testing; releases go through GitHub -> the Kodi repo).
# Restart, not ReloadSkin(): reloading the skin while an add-on's Python is running (e.g. POV still scraping)
# crashes Kodi 22 RC.
# Usage: ./deploy.sh            (uses KODI_HOST or 192.168.1.142)
set -e
HOST="${KODI_HOST:-192.168.1.142}"
SKIN="skin.nocturne.custom"
cd "$(dirname "$0")"

rsync -a --delete --exclude '.DS_Store' "$SKIN/" "root@$HOST:/storage/.kodi/addons/$SKIN/"
rsync -a "$SKIN/keymaps/" "root@$HOST:/storage/.kodi/userdata/keymaps/"
ssh -o BatchMode=yes "root@$HOST" 'systemctl restart kodi'
echo "Deployed $SKIN to $HOST and restarted Kodi."
