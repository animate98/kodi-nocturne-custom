# Keeps the skin's keymap installed: an add-on from a repository can't place files in userdata/keymaps,
# so Timers.xml runs this once per Kodi session (after 90 s idle, when the POV lists have loaded; Kodi 22 RC's
# Python crashes when several scripts start together). Copies keymaps/*.xml to the profile when they differ.
import xbmc
import xbmcvfs

SRC = "special://skin/keymaps/"
DST = "special://profile/keymaps/"

changed = False
_, files = xbmcvfs.listdir(SRC)
if not xbmcvfs.exists(DST):
    xbmcvfs.mkdirs(DST)
for name in files:
    if not name.endswith(".xml"):
        continue
    with xbmcvfs.File(SRC + name) as f:
        new = f.read()
    old = ""
    if xbmcvfs.exists(DST + name):
        with xbmcvfs.File(DST + name) as f:
            old = f.read()
    if new != old:
        with xbmcvfs.File(DST + name, "w") as f:
            f.write(new)
        changed = True
        xbmc.log(f"Nocturne Custom: installed keymap {name}", xbmc.LOGINFO)
if changed:
    xbmc.executebuiltin("Action(reloadkeymaps)")
