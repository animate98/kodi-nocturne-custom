#!/usr/bin/env python3
"""Generate skin.passepartout.custom/1080i/Includes_PovFilmRows.xml: Home > Films > Down from the exhibition.

One POV list at a time, hung like the library's "The hang" (view 500): a row of prints, the focused one large
with its caption. Up / Down move between lists (Up from the first goes back to the exhibition); the list names
stand top right (previous faded, current, next faded). Each row ends with POV's "Next page" item, drawn as a
View all card; Right past the end opens the whole list too, in the View all grid (Custom_1158_PovGrid.xml).

Loading: a row only fetches while it is "visible" (Kodi never loads hidden containers). Rows within one of the
current row are visible (the others are not), drawn at alpha 0, so their first prints decode ahead of you.
Kodi 22 RC's Python crashes when plugin calls start together, so they load one after another: the exhibition,
then the current row, then the row below, then the row above. A loaded row stays loaded.

Run from the repo root:  python3 tools/make_pp_film_rows.py
"""
from pathlib import Path
from xml.sax.saxutils import escape as X

OUT = Path(__file__).resolve().parent.parent / "skin.passepartout.custom/1080i/Includes_PovFilmRows.xml"
POV = "plugin://plugin.video.pov/?mode=build_movie_list&action="

# (title, POV action, may be empty)
ROWS = [
    ("Continue watching", "in_progress_movies", True),
    ("Trending this week", "tmdb_movies_trending", False),
    ("Trending", "trakt_movies_trending", False),
    ("Trending recent", "trakt_movies_trending_recent", False),
    ("Most watched", "trakt_movies_most_watched", False),
    ("Popular", "tmdb_movies_popular", False),
    ("Premieres", "tmdb_movies_premieres", False),
    ("Latest releases", "tmdb_movies_latest_releases", False),
    ("Upcoming", "tmdb_movies_upcoming", False),
    ("Blockbusters", "tmdb_movies_blockbusters", False),
    ("Oscar winners", "tmdb_oscar_winners", False),
    ("Watched", "watched_movies", True),
]
ID0 = 9701              # row i = ID0 + i
EXHIBITION = 9101
ROW_TOP = 160           # the library hang sits at 100; Home leaves room for the list names
CAPTION_TOP = 866
SLIDE = 260              # how far a list travels as it leaves / arrives
PROP = "Window(Home).Property(pp.row)"
N = len(ROWS)


def rid(i):
    return ID0 + i


def url(i):
    return POV + ROWS[i][1]


def grid_url(i):
    """View all: the same list from the grid helper (small posters, 20 a page)."""
    return "plugin://plugin.video.ppgrid/?mode=build_movie_list&action=" + ROWS[i][1]


def loaded(i):
    return f"Integer.IsGreater(Container({rid(i)}).NumItems,0)"


def done(i):
    """Row i finished loading (with or without items). Rows that cannot be empty: has items."""
    if i < 0 or i >= N:
        return "true"
    if ROWS[i][2]:
        return f"[{loaded(i)} | [Control.IsVisible({rid(i)}) + !Container({rid(i)}).IsUpdating]]"
    return loaded(i)


def cur_is(i):
    return f"String.IsEqual({PROP},{i})"


def load_cond(i):
    """When row i may fetch (and is therefore visible)."""
    parts = [loaded(i), cur_is(i),
             f"[{cur_is(i - 1)} + {done(i - 1)}]" if i > 0 else None,            # the row below the current one
             f"[{cur_is(i + 1)} + {done(i + 1)} + {done(i + 2)}]" if i < N - 1 else None]  # the row above, last
    if i == 0:   # on the exhibition: the first two rows, so Down is ready
        parts.append(f"String.IsEmpty({PROP})")
    if i == 1:
        parts.append(f"[String.IsEmpty({PROP}) + {done(0)}]")
    cond = " | ".join(p for p in parts if p)
    return f"$EXP[Home_Films] + $EXP[Home_ExhibitionReady] + [{cond}]"


def nav_down(i):
    """Down from row i: the next row with prints (an empty may-be-empty row is skipped)."""
    out = []
    for j in range(i + 1, N):
        if ROWS[j][2]:
            out.append(f'<ondown condition="{loaded(j)}">{rid(j)}</ondown>')
            out.append(f'<ondown condition="!{loaded(j)}">{rid(j + 1) if j + 1 < N else "noop"}</ondown>')
        else:
            out.append(f'<ondown>{rid(j)}</ondown>')
        break
    return out or ["<ondown>noop</ondown>"]


def nav_up(i):
    if i == 0:
        return [f"<onup>{EXHIBITION}</onup>"]
    j = i - 1
    if ROWS[j][2]:
        alt = rid(j - 1) if j > 0 else EXHIBITION
        return [f'<onup condition="{loaded(j)}">{rid(j)}</onup>', f'<onup condition="!{loaded(j)}">{alt}</onup>']
    return [f"<onup>{rid(j)}</onup>"]


NEXTPAGE = "[String.Contains(ListItem.FileNameAndPath,new_page) | String.StartsWith(ListItem.Label,Next Page)]"

PRINT_SMALL = """\t\t\t\t\t<control type="group">
\t\t\t\t\t\t<left>4</left><top>208</top><width>216</width><height>324</height>
\t\t\t\t\t\t<include content="VidView_PrintBody"><param name="font" value="body_20"/><param name="titlevisible" value="String.IsEmpty(ListItem.Art(poster)) + String.IsEmpty(ListItem.Art(thumb))"/></include>
\t\t\t\t\t</control>"""
PRINT_LARGE = """\t\t\t\t\t<control type="group">
\t\t\t\t\t\t<left>4</left><top>70</top><width>400</width><height>600</height>
\t\t\t\t\t\t<include content="VidView_GrowIn"><param name="cx" value="204"/><param name="cy" value="370"/></include>
\t\t\t\t\t\t<include content="PP_Lift"><param name="anim" value="VidView_LiftIn"/></include>
\t\t\t\t\t\t<include content="VidView_PrintBody"><param name="font" value="body_26"/><param name="titlevisible" value="String.IsEmpty(ListItem.Art(poster)) + String.IsEmpty(ListItem.Art(thumb))"/></include>
\t\t\t\t\t</control>"""


def view_all_card(left, top, w, h, font, focused):
    lift = ('\n\t\t\t\t\t\t<include content="VidView_GrowIn"><param name="cx" value="204"/><param name="cy" value="370"/></include>'
            '\n\t\t\t\t\t\t<include content="PP_Lift"><param name="anim" value="VidView_LiftIn"/></include>') if focused else ""
    return f"""\t\t\t\t\t<control type="group">
\t\t\t\t\t\t<left>{left}</left><top>{top}</top><width>{w}</width><height>{h}</height>{lift}
\t\t\t\t\t\t<control type="image"><left>0</left><top>0</top><right>0</right><bottom>0</bottom><texture colordiffuse="$VAR[C_wash_strong]">common/white.png</texture></control>
\t\t\t\t\t\t<control type="label">
\t\t\t\t\t\t\t<left>16</left><top>0</top><right>16</right><bottom>0</bottom>
\t\t\t\t\t\t\t<align>center</align><aligny>center</aligny><font>{font}</font><textcolor>$VAR[C_ink]</textcolor>
\t\t\t\t\t\t\t<label>View all</label>
\t\t\t\t\t\t</control>
\t\t\t\t\t\t<control type="image"><left>-5</left><top>-5</top><right>-5</right><bottom>-5</bottom><texture border="16" colordiffuse="$VAR[C_bevel]">pp/bevel.png</texture></control>
\t\t\t\t\t</control>"""


def row(i):
    title, action, _ = ROWS[i]
    tags = nav_up(i) + nav_down(i)
    return f"""\t\t<!-- {i}: {X(title)} -->
\t\t<control type="fixedlist" id="{rid(i)}">
\t\t\t<left>-60</left><top>{ROW_TOP}</top><width>2100</width><height>980</height>
\t\t\t<orientation>horizontal</orientation>
\t\t\t<focusposition>2</focusposition>
\t\t\t<scrolltime tween="cubic" easing="out">380</scrolltime>
\t\t\t<preloaditems>2</preloaditems>
\t\t\t<visible>{load_cond(i)}</visible>
\t\t\t<!-- a row above the current one waits slid up and faded, a row below slid down: moving Down, the row you
\t\t\t     leave rises out while the next rises in from below (and the reverse going Up). The arriving row plays
\t\t\t     the same animation reversed, so the ease is symmetric (sine in-out): an ease-out reversed is an ease-in,
\t\t\t     which made the two rows move at different speeds -->
\t\t\t<animation type="Conditional" condition="Integer.IsGreater({PROP},{i})" reversible="true">
\t\t\t\t<effect type="slide" start="0,0" end="0,-{SLIDE}" time="420" tween="sine" easing="inout"/>
\t\t\t\t<effect type="fade" start="100" end="0" time="420" tween="sine" easing="inout"/>
\t\t\t</animation>
\t\t\t<animation type="Conditional" condition="[Integer.IsLess({PROP},{i}) | String.IsEmpty({PROP})]" reversible="true">
\t\t\t\t<effect type="slide" start="0,0" end="0,{SLIDE}" time="420" tween="sine" easing="inout"/>
\t\t\t\t<effect type="fade" start="100" end="0" time="420" tween="sine" easing="inout"/>
\t\t\t</animation>
""" + "".join(f"\t\t\t{t}\n" for t in tags) + f"""\t\t\t<onleft>noop</onleft>
\t\t\t<onright>SetProperty(pp.rowreturn,{rid(i)},home)</onright>
\t\t\t<onright>SetProperty(pp.grid.base,{X(grid_url(i))},home)</onright>
\t\t\t<onright>SetProperty(pp.grid.title,{X(ROWS[i][0])},home)</onright>
\t\t\t<onright>SetProperty(pp.grid.page,1,home)</onright>
\t\t\t<onright>ActivateWindow(1158)</onright>
\t\t\t<onback>{EXHIBITION}</onback>
\t\t\t<onfocus>SetProperty(pp.row,{i},home)</onfocus>
\t\t\t<onfocus>SetProperty(TMDbHelper.WidgetContainer,{rid(i)},home)</onfocus>
\t\t\t<onfocus>SetProperty(TMDbHelper.Colors.SourceImage,Art(poster)|Art(thumb)|Art(fanart),home)</onfocus>
\t\t\t<onclick condition="{NEXTPAGE}">SetProperty(pp.rowreturn,{rid(i)},home)</onclick>
\t\t\t<onclick condition="{NEXTPAGE}">SetProperty(pp.grid.base,{X(grid_url(i))},home)</onclick>
\t\t\t<onclick condition="{NEXTPAGE}">SetProperty(pp.grid.title,{X(ROWS[i][0])},home)</onclick>
\t\t\t<onclick condition="{NEXTPAGE}">SetProperty(pp.grid.page,1,home)</onclick>
\t\t\t<onclick condition="{NEXTPAGE}">ActivateWindow(1158)</onclick>
\t\t\t<onclick condition="!{NEXTPAGE}">Action(Info)</onclick>
\t\t\t<!-- one layout per state; Kodi checks a layout's condition for the whole row, so the View all card and the
\t\t\t     print are both in it, each visible for its own kind of item -->
\t\t\t<itemlayout width="288" height="980">
\t\t\t\t<control type="group"><visible>{NEXTPAGE}</visible>
{view_all_card(4, 208, 216, 324, "cap_20", False)}
\t\t\t\t</control>
\t\t\t\t<control type="group"><visible>!{NEXTPAGE}</visible>
{PRINT_SMALL}
\t\t\t\t</control>
\t\t\t</itemlayout>
\t\t\t<focusedlayout width="472" height="980">
\t\t\t\t<control type="group"><visible>{NEXTPAGE}</visible>
{view_all_card(4, 70, 400, 600, "ttl_40", True)}
\t\t\t\t</control>
\t\t\t\t<control type="group"><visible>!{NEXTPAGE}</visible>
{PRINT_LARGE}
\t\t\t\t</control>
\t\t\t</focusedlayout>
\t\t\t<content target="videos" limit="21">{X(url(i))}</content>
\t\t</control>"""


def names():
    """Top right: previous (faded), current, next (faded) list names."""
    def var(name, pick):
        vals = [f'\t\t<value condition="{cur_is(i)}">{X(pick(i))}</value>' for i in range(N) if pick(i) is not None]
        return f'\t<variable name="{name}">\n' + "\n".join(vals) + "\n\t</variable>"
    cur = var("PovRows_Cur", lambda i: ROWS[i][0])
    # previous / next name where Up / Down really go: an empty may-be-empty row is skipped
    pv, nx = [], []
    for i in range(N):
        if i == 0:
            pv.append(f'\t\t<value condition="{cur_is(0)}">The exhibition</value>')
        else:
            j = i - 1
            if ROWS[j][2]:
                alt = ROWS[j - 1][0] if j > 0 else "The exhibition"
                pv.append(f'\t\t<value condition="{cur_is(i)} + {loaded(j)}">{X(ROWS[j][0])}</value>')
                pv.append(f'\t\t<value condition="{cur_is(i)}">{X(alt)}</value>')
            else:
                pv.append(f'\t\t<value condition="{cur_is(i)}">{X(ROWS[j][0])}</value>')
        if i < N - 1:
            j = i + 1
            cond = f"{cur_is(i)} + {loaded(j)}" if ROWS[j][2] else cur_is(i)
            nx.append(f'\t\t<value condition="{cond}">{X(ROWS[j][0])}</value>')
    prev = '\t<variable name="PovRows_Prev">\n' + "\n".join(pv) + "\n\t</variable>"
    nxt = '\t<variable name="PovRows_Next">\n' + "\n".join(nx) + "\n\t</variable>"
    return "\n".join((prev, cur, nxt))


WHEEL_X, WHEEL_Y, WHEEL_W = 1080, 184, 720   # the current name's box: right edge at 1800, centre y 212
STEP = 50                                    # distance between name centres on screen (the mockup: ~50)
FADED = 28                                   # opacity of the names above / below
SMALL = 67                                   # neighbours at 2/3 size (cap 20 vs 30)


def wheel():
    """The list names top right as a wheel: every name is a label that animates between slots (centre: large and
    dark; one step above / below: smaller and faded; further: gone) whenever the current list changes, with the
    rows' ease so names and rows travel together."""
    cy = WHEEL_Y + 28
    rx = WHEEL_X + WHEEL_W
    t = 'time="420" tween="sine" easing="inout"'

    def anim(cond, dy, alpha):
        # Kodi applies the shrink after the slide, around the centre line, which pulls a name back towards
        # the centre by the same factor: slide further so it lands dy away
        dy = round(dy * 100 / SMALL)
        return (f'\t\t\t\t<animation type="Conditional" condition="{cond}" reversible="true">\n'
                f'\t\t\t\t\t<effect type="zoom" start="100" end="{SMALL}" center="{rx},{cy}" {t}/>\n'
                f'\t\t\t\t\t<effect type="slide" start="0,0" end="0,{dy}" {t}/>\n'
                f'\t\t\t\t\t<effect type="fade" start="100" end="{alpha}" {t}/>\n'
                f'\t\t\t\t</animation>\n')

    labels = [(-1, "The exhibition")] + [(i, ROWS[i][0]) for i in range(N)]
    out = ['\t\t<!-- list names, top right: an animated wheel -->', '\t\t<control type="group">']
    for i, name in labels:
        if i == -1:
            above = f"[{cur_is(0)} | [{cur_is(1)} + !{loaded(0)}]]"
            far_above = f"![{above}]"
            below = far_below = None
            vis = "true"
        else:
            above = cur_is(i + 1) if i < N - 1 else None
            far_above = f"Integer.IsGreater({PROP},{i + 1})"
            below = cur_is(i - 1) if i > 0 else None
            far_below = f"[Integer.IsLess({PROP},{i - 1}) | String.IsEmpty({PROP})]" if i > 0 else f"String.IsEmpty({PROP})"
            vis = loaded(i) if ROWS[i][2] else "true"
        out.append(f'\t\t\t<control type="label">')
        out.append(f'\t\t\t\t<left>{WHEEL_X}</left><top>{WHEEL_Y}</top><width>{WHEEL_W}</width><height>56</height>'
                   f'<align>right</align><aligny>center</aligny>')
        out.append(f'\t\t\t\t<font>capw_30</font><textcolor>$VAR[C_ink]</textcolor><label>{X(name)}</label>')
        out.append(f'\t\t\t\t<visible>{vis}</visible>')
        block = ""
        if above:
            block += anim(above, -STEP, FADED)
        if far_above:
            block += anim(far_above, -2 * STEP, 0)
        if below:
            block += anim(below, STEP, FADED)
        if far_below:
            block += anim(far_below, 2 * STEP, 0)
        out.append(block.rstrip("\n"))
        out.append('\t\t\t</control>')
    out.append('\t\t</control>')
    return "\n".join(out)


def main():
    in_rows = " | ".join(f"Control.HasFocus({rid(i)})" for i in range(N))
    # Down from the exhibition: back to the row you left, else the first row with prints
    ex_down = [f'\t\t<ondown condition="$EXP[Home_Films] + {cur_is(i)} + {loaded(i)}">{rid(i)}</ondown>' for i in range(N)]
    ex_down.append(f'\t\t<ondown condition="$EXP[Home_Films] + [String.IsEmpty({PROP}) | ![{" | ".join(f"[{cur_is(i)} + {loaded(i)}]" for i in range(N))}]] + {loaded(0)}">{rid(0)}</ondown>')
    ex_down.append(f'\t\t<ondown condition="$EXP[Home_Films] + [String.IsEmpty({PROP}) | ![{" | ".join(f"[{cur_is(i)} + {loaded(i)}]" for i in range(N))}]] + !{loaded(0)}">{rid(1)}</ondown>')
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GENERATED by tools/make_pp_film_rows.py - edit that script, not this file. -->
<includes>
\t<expression name="Home_InFilmRows">{in_rows}</expression>
{names()}
\t<include name="Home_FilmRowsExhibitionDown">
{chr(10).join(ex_down)}
\t</include>
\t<include name="Home_FilmRows">
\t<control type="group">
\t\t<visible>$EXP[Home_Films]</visible>
\t\t<!-- the rows load while you are on the exhibition too (alpha 0), so Down is instant -->
\t\t<animation effect="fade" start="100" end="0" time="200" condition="!$EXP[Home_InFilmRows]">Conditional</animation>
{wheel()}
{chr(10).join(row(i) for i in range(N))}
\t\t<!-- caption of the focused print (the library hang's), or View all -->
\t\t<control type="group">
\t\t\t<visible>$EXP[Home_InFilmRows] + !{NEXTPAGE.replace('ListItem.', 'Container.ListItem.')}</visible>
\t\t\t<include content="Title_Hang"><param name="left" value="520"/><param name="top" value="{CAPTION_TOP}"/></include>
\t\t\t<include content="VidView_Caption"><param name="left" value="520"/><param name="top" value="{CAPTION_TOP}"/><param name="width" value="1280"/></include>
\t\t</control>
\t\t<control type="group">
\t\t\t<visible>$EXP[Home_InFilmRows] + {NEXTPAGE.replace('ListItem.', 'Container.ListItem.')}</visible>
\t\t\t<control type="label">
\t\t\t\t<left>504</left><top>{CAPTION_TOP}</top><width>1296</width><height>84</height><textoffsetx>16</textoffsetx>
\t\t\t\t<font>ttl_72</font><textcolor>$VAR[C_ink]</textcolor><label>View all</label>
\t\t\t</control>
\t\t\t<control type="label">
\t\t\t\t<left>520</left><top>{CAPTION_TOP + 96}</top><width>1280</width><height>28</height>
\t\t\t\t<font>cap_20</font><textcolor>$VAR[C_ink]</textcolor><label>$VAR[PovRows_Cur]</label>
\t\t\t</control>
\t\t</control>
\t</control>
\t</include>
</includes>
"""
    OUT.write_text(xml)
    print(f"wrote {OUT.name}: {N} rows")


if __name__ == "__main__":
    main()
