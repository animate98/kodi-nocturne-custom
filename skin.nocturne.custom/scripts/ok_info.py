# OK in the video library: films, shows and episodes open Kodi's info page instead of playing / browsing.
# POV runs its own play screen when a title is clicked, which skips Kodi's "Default select action" setting,
# so keymaps/nocturne_ok.xml sends OK in the Videos window here first. Everything else (menus, genres,
# seasons, the options bar) gets a normal OK.
import xbmc

VIEWS = (50, 500, 501, 502, 503, 506, 507)   # Nocturne's video views (MyVideoNav.xml)
INFO_TYPES = ("movie", "tvshow", "episode")

in_view = any(xbmc.getCondVisibility(f"Control.HasFocus({v})") for v in VIEWS)
dbtype = xbmc.getInfoLabel("ListItem.DBType")
if in_view and dbtype in INFO_TYPES and not xbmc.getCondVisibility("ListItem.IsParentFolder"):
    xbmc.executebuiltin("Action(Info)")
else:
    xbmc.executebuiltin("Action(Select)")
