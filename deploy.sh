#!/bin/sh
# Sync the skin to the CoreELEC box and reload it in Kodi.
# Usage: ./deploy.sh            (uses KODI_HOST or 192.168.1.142)
set -e
HOST="${KODI_HOST:-192.168.1.142}"
SKIN="skin.nocturne.custom"
cd "$(dirname "$0")"

rsync -a --delete --exclude '.DS_Store' "$SKIN/" "root@$HOST:/storage/.kodi/addons/$SKIN/"
rsync -a "$SKIN/keymaps/" "root@$HOST:/storage/.kodi/userdata/keymaps/"
ssh -o BatchMode=yes "root@$HOST" 'kodi-send --action="Action(reloadkeymaps)" >/dev/null; kodi-send --action="ReloadSkin()" >/dev/null'
echo "Deployed $SKIN to $HOST and reloaded the skin."
