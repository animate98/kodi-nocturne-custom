#!/usr/bin/env python3
"""Generate skin.passepartout.custom/1080i/Custom_1158_PovGrid.xml: "View all" for a POV list.

The Salon's prints on a 2 x 10 grid, one page (20 titles) at a time, from the grid helper
(plugin.video.ppgrid: POV's lists with small "gridposter" art and no "Next page" item). Header: POV and Options
(the selected film's menu); the list name left, "Page N" right; chevrons at the sides; the caption of the print
in focus at the bottom.

Pages: three panels take turns. Page n lives in panel n % 3, so around the current page the previous and the next
are already loaded (they wait off to the side, faded). Right past the 10th print of a row slides the current
page out to the left and the next one in from the right (Left: the reverse); the panel that held the old
previous page then loads the new next one while it is hidden. Loading order: the current page, then the next,
then the previous (one plugin call at a time: Kodi 22 RC's Python crashes when calls start together).

Opened from Home's Films rows with
  SetProperty(pp.grid.base,plugin://plugin.video.ppgrid/?mode=...&action=...,home)
  SetProperty(pp.grid.title,<name>,home) SetProperty(pp.grid.page,1,home) ActivateWindow(1158)
POV does not tell the skin how many pages a list has: "Page N" only; Right goes on while a page is full (20).

Run from the repo root:  python3 tools/make_pp_grid.py
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "skin.passepartout.custom/1080i/Custom_1158_PovGrid.xml"
WIN = 1158
PANELS = (9780, 9781, 9782)      # page n -> PANELS[n % 3]
OPTIONS = 9771
MAX_PAGES = 60
COLS, ROWS = 10, 2
PER_PAGE = COLS * ROWS
LEFT, WIDTH = 120, 1680
CELL_W = WIDTH // COLS           # 168
PW, PH = 136, 204                # print (2:3)
CELL_H = PH + 36
TOP = 300
SLIDE = 420                      # how far a page travels as it leaves / arrives
T = 'time="440" tween="sine" easing="inout"'
PAGE = "Window(Home).Property(pp.grid.page)"
BASE = "Window(Home).Property(pp.grid.base)"


def page_is(n):
    return f"String.IsEqual({PAGE},{n})"


def any_page(ns):
    ns = list(ns)
    return "[" + " | ".join(page_is(n) for n in ns) + "]" if ns else "false"


def pid(k):
    return PANELS[k]


def loaded(k):
    return f"Integer.IsGreater(Container({pid(k)}).NumItems,0)"


def full(k):
    return f"Integer.IsGreater(Container({pid(k)}).NumItems,{PER_PAGE - 1})"


PAGES = range(1, MAX_PAGES + 1)


def role(k, r):
    """Pages n for which panel k holds page n + r (r = -1 previous, 0 current, +1 next)."""
    # page 0 counts as a (blank) previous page: on page 1 the spare panel still parks at the left, faded. Without
    # a place it would sit in the middle, and coming back from page 2 it slid page 3's prints in behind page 1.
    return any_page(n for n in PAGES if (n + r) % 3 == k and 0 <= n + r <= MAX_PAGES)


def path_var(k):
    vals = []
    for n in PAGES:
        cur = n % 3
        for r in (-1, 0, 1):
            p = n + r
            if p < 1 or p % 3 != k:
                continue
            url = f"$INFO[{BASE}]" + (f"&amp;new_page={p}" if p > 1 else "")
            if r == 0:
                cond = page_is(n)
            elif r == 1:    # the next page: once the current one is in, and full
                cond = f"{page_is(n)} + {full(cur)}"
            else:           # the previous page: last, after the next one (or when there is none)
                nxt = (n + 1) % 3
                cond = f"{page_is(n)} + {loaded(cur)} + [{loaded(nxt)} | !{full(cur)}]"
            vals.append(f'\t\t<value condition="{cond}">{url}</value>')
    return f'\t<variable name="PovGrid_Path{k}">\n' + "\n".join(vals) + "\n\t</variable>"


def panel(k):
    me, nxt_k, prv_k = pid(k), (k + 1) % 3, (k - 1) % 3
    # Right past the last column: the next page (already loaded), focus on the same row's first print
    right = [f'<onright condition="{page_is(n)} + {full(k)} + {loaded(nxt_k)}">SetProperty(pp.grid.page,{n + 1},home)</onright>'
             for n in PAGES if n % 3 == k and n < MAX_PAGES]
    right += [f'<onright condition="{full(k)} + {loaded(nxt_k)} + Integer.IsEqual(Container({me}).CurrentItem,{r * COLS + COLS})">'
              f'SetFocus({pid(nxt_k)},{r * COLS},absolute)</onright>' for r in range(ROWS)]
    left = [f'<onleft condition="{page_is(n)} + {loaded(prv_k)}">SetProperty(pp.grid.page,{n - 1},home)</onleft>'
            for n in PAGES if n % 3 == k and n > 1]
    left += [f'<onleft condition="!{page_is(1)} + {loaded(prv_k)} + Integer.IsEqual(Container({me}).CurrentItem,{r * COLS + 1})">'
             f'SetFocus({pid(prv_k)},{r * COLS + COLS - 1},absolute)</onleft>' for r in range(ROWS)]
    px = (CELL_W - PW) // 2
    cx, cy = px + PW // 2, 22 + PH // 2
    body = ('<include content="VidView_PrintBody"><param name="font" value="body_20"/>'
            '<param name="art" value="$VAR[PovGrid_Art]"/>'
            '<param name="titlevisible" value="String.IsEmpty(ListItem.Art(gridposter)) + String.IsEmpty(ListItem.Art(poster))"/></include>')
    nav = "".join(f"\t\t\t{t}\n" for t in right + ["<onright>noop</onright>"] + left + ["<onleft>noop</onleft>"])
    return f"""\t\t<!-- panel {k}: pages n with n % 3 == {k} -->
\t\t<control type="panel" id="{me}">
\t\t\t<left>{LEFT}</left><top>{TOP}</top><width>{WIDTH}</width><height>{CELL_H * ROWS}</height>
\t\t\t<orientation>vertical</orientation>
\t\t\t<scrolltime tween="cubic" easing="out">300</scrolltime>
\t\t\t<preloaditems>0</preloaditems>
\t\t\t<!-- waiting as the previous page: off to the left, faded; as the next: to the right. The arriving page
\t\t\t     plays the same animation reversed, so the ease is symmetric. A panel that is loading (it just became
\t\t\t     the new next / previous page) is hidden outright, so it never crosses the page on show. -->
\t\t\t<animation type="Conditional" condition="{role(k, -1)}" reversible="true">
\t\t\t\t<effect type="slide" start="0,0" end="-{SLIDE},0" {T}/>
\t\t\t\t<effect type="fade" start="100" end="0" {T}/>
\t\t\t</animation>
\t\t\t<animation type="Conditional" condition="{role(k, 1)}" reversible="true">
\t\t\t\t<effect type="slide" start="0,0" end="{SLIDE},0" {T}/>
\t\t\t\t<effect type="fade" start="100" end="0" {T}/>
\t\t\t</animation>
\t\t\t<animation effect="fade" start="100" end="0" time="0" condition="Container({me}).IsUpdating | !{loaded(k)}">Conditional</animation>
\t\t\t<onup>{OPTIONS}</onup>
\t\t\t<ondown>noop</ondown>
{nav}\t\t\t<onclick>Action(Info)</onclick>
\t\t\t<onfocus>SetProperty(TMDbHelper.WidgetContainer,{me},home)</onfocus>
\t\t\t<itemlayout width="{CELL_W}" height="{CELL_H}">
\t\t\t\t<control type="group">
\t\t\t\t\t<left>{px}</left><top>22</top><width>{PW}</width><height>{PH}</height>
\t\t\t\t\t{body}
\t\t\t\t</control>
\t\t\t</itemlayout>
\t\t\t<focusedlayout width="{CELL_W}" height="{CELL_H}">
\t\t\t\t<control type="group">
\t\t\t\t\t<left>{px}</left><top>22</top><width>{PW}</width><height>{PH}</height>
\t\t\t\t\t<animation type="Focus" reversible="false" condition="!Skin.HasSetting(passepartout.reducemotion)">
\t\t\t\t\t\t<effect type="zoom" start="100" end="112" center="{cx},{cy}" time="260" tween="cubic" easing="out"/>
\t\t\t\t\t</animation>
\t\t\t\t\t<animation type="Conditional" condition="Skin.HasSetting(passepartout.reducemotion) + Control.HasFocus({me})">
\t\t\t\t\t\t<effect type="zoom" start="100" end="112" center="{cx},{cy}" time="0"/>
\t\t\t\t\t</animation>
\t\t\t\t\t<animation type="Unfocus" condition="!Skin.HasSetting(passepartout.reducemotion)">
\t\t\t\t\t\t<effect type="zoom" start="112" end="100" center="{cx},{cy}" time="160"/>
\t\t\t\t\t</animation>
\t\t\t\t\t<control type="image">
\t\t\t\t\t\t<left>-24</left><top>-12</top><right>-24</right><bottom>-40</bottom>
\t\t\t\t\t\t<texture border="64,48,64,76" colordiffuse="$VAR[ShadowColor]">pp/lift_xs.png</texture>
\t\t\t\t\t\t<visible>Control.HasFocus({me}) + !Skin.HasSetting(passepartout.noshadow)</visible>
\t\t\t\t\t</control>
\t\t\t\t\t{body}
\t\t\t\t</control>
\t\t\t</focusedlayout>
\t\t\t<content target="videos">$VAR[PovGrid_Path{k}]</content>
\t\t</control>"""


def main():
    cur_role = {k: role(k, 0) for k in range(3)}
    focus_cur = "\n".join(f'\t<onload condition="{cur_role[k]}">SetFocus({pid(k)})</onload>' for k in range(3))
    header_down = "\n".join(f'\t\t\t<ondown condition="{cur_role[k]}">{pid(k)}</ondown>' for k in range(3))
    options_click = "\n".join(f'\t\t\t\t<onclick condition="{cur_role[k]}">SetFocus({pid(k)})</onclick>' for k in range(3))
    cur_full = "[" + " | ".join(f"[{cur_role[k]} + {full(k)}]" for k in range(3)) + "]"
    cur_waiting = "[" + " | ".join(f"[{cur_role[k]} + [Container({pid(k)}).IsUpdating | !{loaded(k)}]]" for k in range(3)) + "]"
    in_grid = "[" + " | ".join(f"Control.HasFocus({pid(k)})" for k in range(3)) + "]"
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GENERATED by tools/make_pp_grid.py - edit that script, not this file.
	View all for a POV list (opened from Home's Films rows): the Salon's prints, 2 x 10, a page at a time. -->
<window id="{WIN}">
	<defaultcontrol always="true">{PANELS[1]}</defaultcontrol>
{focus_cur}
	<onload>SetProperty(TMDbHelper.Colors.SourceImage,Art(gridposter)|Art(poster)|Art(thumb),home)</onload>
	<onunload>ClearProperty(TMDbHelper.WidgetContainer,home)</onunload>
	<include>Anim_WindowOpenClose</include>
	<controls>
		<include>PP_Background</include>

		<!-- header: POV (where you are) and Options (the selected film's menu) -->
		<control type="grouplist">
			<left>120</left><top>56</top><width>1400</width><height>44</height>
			<orientation>horizontal</orientation><itemgap>20</itemgap><usecontrolcoords>true</usecontrolcoords>
{header_down}
			<control type="button">
				<top>10</top><width max="560">auto</width><height>34</height>
				<font>cap_20</font><textcolor>$VAR[C_ink]</textcolor><disabledcolor>$VAR[C_ink]</disabledcolor>
				<textoffsetx>0</textoffsetx><aligny>top</aligny>
				<texturefocus border="0,0,0,2" colordiffuse="$VAR[C_ink]">pp/underline.png</texturefocus>
				<texturenofocus border="0,0,0,2" colordiffuse="$VAR[C_ink]">pp/underline.png</texturenofocus>
				<label>POV</label>
				<enable>false</enable>
			</control>
			<control type="image"><width>16</width><height>44</height><texture/></control>
			<control type="button" id="{OPTIONS}">
				<width>auto</width><height>44</height>
				<font>cap_20</font><textcolor>$VAR[C_ink2]</textcolor><focusedcolor>$VAR[PaperColor]</focusedcolor>
				<textoffsetx>16</textoffsetx><aligny>center</aligny>
				<texturefocus colordiffuse="$VAR[C_ink]">common/white.png</texturefocus>
				<texturenofocus/>
				<label>Options</label>
{options_click}
				<onclick>Action(ContextMenu)</onclick>
			</control>
		</control>
		<include>PP_Clock</include>

		<!-- the list name and the page -->
		<control type="label">
			<left>120</left><top>190</top><width>1200</width><height>48</height><aligny>center</aligny>
			<font>capw_30</font><textcolor>$VAR[C_ink2]</textcolor>
			<label>$INFO[Window(Home).Property(pp.grid.title)]</label>
		</control>
		<control type="label">
			<left>1200</left><top>190</top><width>600</width><height>48</height><align>right</align><aligny>center</aligny>
			<font>body_28</font><textcolor>$VAR[C_ink2]</textcolor>
			<label>Page $INFO[{PAGE}]</label>
		</control>

		<!-- previous / next page: the chevron from media/custom (bi chevron-compact-right, white, tinted with the ink;
		     the left one is its mirror). 120 x 120 image, the stroke is about 31 x 98 of it -->
		<control type="image">
			<left>{56 - 60}</left><top>{TOP + CELL_H - 60}</top><width>120</width><height>120</height>
			<aspectratio>keep</aspectratio>
			<texture colordiffuse="$VAR[C_ink2]">custom/chevron_left.png</texture>
			<visible>!{page_is(1)} + !String.IsEmpty({PAGE})</visible>
		</control>
		<control type="image">
			<left>{1864 - 60}</left><top>{TOP + CELL_H - 60}</top><width>120</width><height>120</height>
			<aspectratio>keep</aspectratio>
			<texture colordiffuse="$VAR[C_ink2]">custom/chevron_right.png</texture>
			<visible>{cur_full}</visible>
		</control>

		<!-- the pages: the previous and next wait faded out at the sides -->
		<control type="group">
			<left>0</left><top>0</top><width>1920</width><height>1080</height>
{chr(10).join(panel(k) for k in range(3))}
		</control>
		<control type="label">
			<left>120</left><top>{TOP + 180}</top><width>1680</width><height>60</height><align>center</align><aligny>center</aligny>
			<font>cap_20</font><textcolor>$VAR[C_ink2]</textcolor><label>Hanging…</label>
			<visible>{cur_waiting} + !String.IsEmpty({BASE})</visible>
		</control>

		<!-- caption of the print in focus -->
		<control type="label">
			<left>120</left><top>924</top><width>1680</width><height>60</height>
			<font>ttl_44</font><textcolor>$VAR[C_ink]</textcolor>
			<label>$INFO[Container.ListItem.Label]</label>
			<visible>{in_grid}</visible>
		</control>
		<control type="label">
			<left>120</left><top>990</top><width>1680</width><height>30</height>
			<font>cap_20</font><textcolor>$VAR[C_ink2]</textcolor>
			<label>$VAR[VidView_Cap]</label>
			<visible>{in_grid}</visible>
		</control>
	</controls>
</window>
"""
    vars_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GENERATED by tools/make_pp_grid.py - edit that script, not this file. -->
<includes>
\t<!-- the grid helper's small poster (TMDb w342), POV's own as the fallback -->
\t<variable name="PovGrid_Art">
\t\t<value condition="!String.IsEmpty(ListItem.Art(gridposter))">$INFO[ListItem.Art(gridposter)]</value>
\t\t<value>$INFO[ListItem.Art(poster)]</value>
\t</variable>
{chr(10).join(path_var(k) for k in range(3))}
</includes>
"""
    OUT.write_text(xml)
    (OUT.parent / "Includes_PovGrid.xml").write_text(vars_xml)
    print(f"wrote {OUT.name} and Includes_PovGrid.xml")


if __name__ == "__main__":
    main()
