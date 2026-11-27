"""Passe-partout grid helper: one page of a POV list, with small posters.

    plugin://plugin.video.ppgrid/?mode=build_movie_list&action=tmdb_movies_trending&new_page=2

The parameters are POV's own. POV's list code runs here, in this add-on's Python - not as a second plugin call:
Kodi 22 RC's Python crashes when two add-on interpreters start or stop together, and asking POV for the list
would be exactly that. Every title gets art "gridposter" = the TMDb poster at w342 (POV's "poster" stays as it
is, full size, for the info page). POV's "Next page" item is left out, and the play links stay POV's.
"""
import re
import sys

import xbmcaddon
import xbmcplugin
import xbmcvfs

POV = "plugin.video.pov"

# POV's code asks Kodi "which add-on am I?" through xbmcaddon.Addon(); here that would be this helper
_Addon = xbmcaddon.Addon
xbmcaddon.Addon = lambda id="", *a, **k: _Addon(id or POV)

sys.path.insert(0, xbmcvfs.translatePath(f"special://home/addons/{POV}/resources/lib"))

from urllib.parse import parse_qsl  # noqa: E402
from modules import kodi_utils  # noqa: E402

SMALL = re.compile(r"(image\.tmdb\.org/t/p/)[^/]+/")


def add_items(handle, item_list):
    for _url, listitem, _folder in item_list:
        poster = listitem.getArt("poster")
        if poster and "image.tmdb.org/t/p/" in poster:
            listitem.setArt({"gridposter": SMALL.sub(r"\1w342/", poster)})
    xbmcplugin.addDirectoryItems(handle, item_list)


def add_dir(handle, url_params, *args, **kwargs):
    if "new_page" in url_params:
        return  # one page per call: the grid pages itself
    return _add_dir(handle, url_params, *args, **kwargs)


_add_dir = kodi_utils.add_dir
kodi_utils.add_items = add_items
kodi_utils.add_dir = add_dir
kodi_utils.set_view_mode = lambda *a, **k: None   # the skin's window, not a view to switch

ROUTES = {
    "build_movie_list": ("menus.movies", "Menu"),
    "build_tvshow_list": ("menus.tvshows", "Menu"),
}

params = dict(parse_qsl(sys.argv[2][1:]))
route = ROUTES.get(params.get("mode"))
if route:
    module = __import__(route[0], fromlist=[route[1]])
    getattr(module, route[1])(params).run()
else:
    xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=False)
