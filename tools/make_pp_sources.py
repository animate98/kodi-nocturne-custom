#!/usr/bin/env python3
"""Generate POV's source picker and loading screen in Passe-partout's own look.

POV opens these with xbmcgui.WindowXMLDialog("sources_results.xml" / "progress_media.xml", <POV's folder>):
Kodi looks for a file of that name in the active skin first, so the skin's copies replace POV's. They keep the
ids POV's code fills or reads; everything around them is the skin's.

  sources_results.xml  list 2000 (POV's "List" style; 2001 / 2002 for its other styles), scrollbar 2060.
                       Per source (ListItem.Property): tikiskins.quality, .provider, .name, .size_label,
                       .source_type, .source_site, .extra_info, .count; the "full search" row has
                       .perform_full_search and .start_full_scrape. Window: tikiskins.title, .plot, .poster,
                       .total_results, .scrape_time, .window_style.
  progress_media.xml   textbox 2000 (POV's text), progress 5000, buttons 10 / 11 (only for POV's questions,
                       e.g. resume), window tikiskins.source_progress.* (title, year, poster...). No plot.

The page continues the wall label: the matted print lined up with the breadcrumb, the film's description under
it (static: no scrolling), the title and a museum caption on the right, the sources as a catalogue below.

Badges: each source row has fixed badge columns (Kodi lists can't flow images), matched on POV's details line
(extra_info) and the release name. Kodi's String.Contains is case-insensitive but can't take "+" (HDR10+ is
matched as HDR10, DD+ from the release name: DDP / EAC3). Text badges by default; with Skin setting
pp.logobadges the logo badge images in special://profile/addon_data/skin.passepartout.custom/badges/ (installed
on the box only, see tools/make_badges.py) replace them.

Run from the repo root:  python3 tools/make_pp_sources.py
"""
from pathlib import Path
from xml.sax.saxutils import escape as X

OUT = Path(__file__).resolve().parent.parent / "skin.passepartout.custom/1080i"
X_ = "ListItem.Property(tikiskins.extra_info)"
N_ = "ListItem.Property(tikiskins.name)"
LOGOS = "special://profile/addon_data/skin.passepartout.custom/badges/"


def has(field, *words):
    return "[" + " | ".join(f"String.Contains({field},{w})" for w in words) + "]"


def no(field, *words):
    return " + ".join(f"!String.Contains({field},{w})" for w in words)


# column: (name, width, [(text, logo file, condition), ...]) - the first match wins
DV = has(X_, "D/VISION")
BADGES = [
    ("visual", 142, [
        ("Dolby Vision", "dv", DV),
        ("HDR10+", "hdr10plus", f"!{DV} + {has(X_, 'HDR10')}"),
        ("HDR", "hdr", f"!{DV} + {no(X_, 'HDR10', 'HDRIP')} + {has(X_, 'HDR')}"),
        ("SDR", "sdr", has(X_, "SDR")),
    ]),
    ("imax", 112, [
        ("IMAX Enh.", "imax-enhanced", has(N_, "IMAX ENHANCED")),
        ("IMAX", "imax", has(N_, "IMAX")),
    ]),
    ("source", 96, [
        ("Remux", "remux", has(X_, "REMUX")),
        ("BluRay", "bluray", has(X_, "BLURAY")),
        ("WebRip", "webrip", f"{has(X_, 'WEB')} + {has(N_, 'WEBRIP', 'WEB RIP')}"),
        ("WEB-DL", "webdl", has(X_, "WEB")),
        ("HDTV", "hdtv", has(X_, "HDTV", "PDTV")),
        ("DVDRip", "dvdrip", has(X_, "DVD")),
    ]),
    ("codec", 72, [
        ("HEVC", "hevc", has(X_, "HEVC")),
        ("H.264", "h264", has(X_, "AVC")),
        ("AV1", "av1", has(X_, "AV1")),
        ("XviD", "xvid", has(X_, "XVID", "DIVX")),
    ]),
    ("audio", 120, [
        ("Atmos", "atmos", has(X_, "ATMOS")),
        ("DTS:X", "dtsx", has(X_, "DTS-X")),
        ("DTS-HD MA", "dtshdma", has(X_, "DTS-HD MA")),
        ("DTS-HD", "dtshd", has(X_, "DTS-HD")),
        ("DTS", "dts", has(X_, "DTS")),
        ("DD+", "ddplus", has(N_, "DDP", "EAC3", "E AC3")),
        ("DD", "dd", has(X_, "DD")),
    ]),
    ("truehd", 90, [
        ("TrueHD", "truehd", has(X_, "TRUEHD")),
    ]),
    ("channels", 52, [
        ("7.1", "71", has(X_, "8CH")),
        ("6.1", "61", has(X_, "7CH")),
        ("5.1", "51", has(X_, "6CH")),
    ]),
    ("tenbit", 72, [
        ("10-bit", "10bit", has(N_, "10BIT", "10 BIT")),
    ]),
]
GAP = 10
BADGE_H = 26


def variables():
    out = []
    for name, _w, options in BADGES:
        t = [f'\t\t<value condition="{c}">{X(text)}</value>' for text, _f, c in options]
        f = [f'\t\t<value condition="{c}">{LOGOS}{file}.png</value>' for _t, file, c in options]
        out.append(f'\t<variable name="PovBadge_{name}_Text">\n' + "\n".join(t) + "\n\t</variable>")
        out.append(f'\t<variable name="PovBadge_{name}_Logo">\n' + "\n".join(f) + "\n\t</variable>")
        out.append(f'\t<expression name="PovBadge_{name}_Any">' + " | ".join(f"[{c}]" for _t, _f, c in options) + '</expression>')
    return "\n".join(out)


def badge_strip(left, top, on):
    """One row's badge columns. on: the selected (ink) row, so the badges turn paper-coloured."""
    ink = "on_ink" if on else "ink2"
    edge = "on_ink" if on else "rule_strong"
    x, parts = left, []
    for name, w, _opts in BADGES:
        txt = f"$VAR[PovBadge_{name}_Text]"
        parts.append(f"""\t\t\t\t\t<control type="group">
\t\t\t\t\t\t<left>{x}</left><top>{top}</top><width>{w}</width><height>{BADGE_H}</height>
\t\t\t\t\t\t<visible>$EXP[PovBadge_{name}_Any]</visible>
\t\t\t\t\t\t<control type="group">
\t\t\t\t\t\t\t<visible>!Skin.HasSetting(pp.logobadges)</visible>
\t\t\t\t\t\t\t<control type="image"><left>0</left><top>0</top><width>{w}</width><height>{BADGE_H}</height><texture border="2" colordiffuse="{edge}">pp/frame_1.png</texture></control>
\t\t\t\t\t\t\t<control type="label"><left>0</left><top>0</top><width>{w}</width><height>{BADGE_H}</height><align>center</align><aligny>center</aligny><font>cap_16</font><textcolor>{ink}</textcolor><label>{txt}</label></control>
\t\t\t\t\t\t</control>
\t\t\t\t\t\t<control type="image">
\t\t\t\t\t\t\t<left>0</left><top>2</top><width>{w}</width><height>{BADGE_H - 4}</height><aspectratio align="left" aligny="center">keep</aspectratio>
\t\t\t\t\t\t\t<texture colordiffuse="{'on_ink' if on else 'ink'}">$VAR[PovBadge_{name}_Logo]</texture>
\t\t\t\t\t\t\t<visible>Skin.HasSetting(pp.logobadges)</visible>
\t\t\t\t\t\t</control>
\t\t\t\t\t</control>""")
        x += w + GAP
    return "\n".join(parts)


FULL = "!String.IsEmpty(ListItem.Property(tikiskins.perform_full_search))"
ROW_H, LIST_TOP, LIST_LEFT, LIST_W, ROWS = 104, 330, 640, 1160, 6


def row(on):
    num = "ink3" if not on else "on_ink"
    ink = "on_ink" if on else "ink"
    body = "on_ink" if on else "body"
    soft = "on_ink" if on else "ink2"
    fade = '\n\t\t\t\t\t\t<animation effect="fade" start="100" end="62" time="0" condition="true">Conditional</animation>' if on else ""
    bg = (f'\t\t\t\t\t<control type="image"><left>0</left><top>0</top><width>{LIST_W}</width><height>{ROW_H}</height>'
          f'<texture colordiffuse="ink">common/white.png</texture></control>\n') if on else (
          f'\t\t\t\t\t<control type="image"><left>0</left><top>{ROW_H - 1}</top><width>{LIST_W}</width><height>1</height>'
          f'<texture colordiffuse="rule_row">common/white.png</texture></control>\n')
    return f"""{bg}\t\t\t\t\t<control type="group">
\t\t\t\t\t\t<visible>!{FULL}</visible>
\t\t\t\t\t\t<control type="label"><left>20</left><top>0</top><width>50</width><height>{ROW_H}</height><aligny>center</aligny><font>mono_22</font><textcolor>{num}</textcolor><label>$INFO[ListItem.Property(tikiskins.count)]</label>{fade}</control>
\t\t\t\t\t\t<control type="label"><left>84</left><top>14</top><width>146</width><height>48</height><aligny>center</aligny><font>ttl_40</font><textcolor>{ink}</textcolor><label>$INFO[ListItem.Property(tikiskins.quality)]</label></control>
\t\t\t\t\t\t<control type="label"><left>84</left><top>64</top><width>146</width><height>24</height><aligny>center</aligny><font>cap_16</font><textcolor>{soft}</textcolor><label>$INFO[ListItem.Property(tikiskins.provider)]</label>{fade}</control>
\t\t\t\t\t\t<control type="label"><left>234</left><top>14</top><width>470</width><height>36</height><aligny>center</aligny><font>body_24</font><textcolor>{body}</textcolor><label>$INFO[ListItem.Property(tikiskins.name)]</label></control>
\t\t\t\t\t\t<control type="label"><left>720</left><top>14</top><width>{LIST_W - 720 - 28}</width><height>36</height><align>right</align><aligny>center</aligny><font>cap_20</font><textcolor>{soft}</textcolor><label>$INFO[ListItem.Property(tikiskins.size_label)]$INFO[ListItem.Property(tikiskins.source_type),  ·  ]$INFO[ListItem.Property(tikiskins.source_site),  ·  ]</label>{fade}</control>
{badge_strip(234, 62, on)}
\t\t\t\t\t</control>
\t\t\t\t\t<control type="label">
\t\t\t\t\t\t<left>84</left><top>0</top><width>{LIST_W - 112}</width><height>{ROW_H}</height><aligny>center</aligny>
\t\t\t\t\t\t<font>cap_20</font><textcolor>{ink}</textcolor><label>$INFO[ListItem.Property(tikiskins.start_full_scrape)]</label>
\t\t\t\t\t\t<visible>{FULL}</visible>
\t\t\t\t\t</control>"""


def results_list(lid, style):
    return f"""\t\t<control type="fixedlist" id="{lid}">
\t\t\t<left>{LIST_LEFT}</left><top>{LIST_TOP}</top><width>{LIST_W}</width><height>{ROW_H * ROWS}</height>
\t\t\t<orientation>vertical</orientation>
\t\t\t<focusposition>0</focusposition>
\t\t\t<movement>{ROWS - 1}</movement>
\t\t\t<scrolltime tween="cubic" easing="out">260</scrolltime>
\t\t\t<pagecontrol>{lid + 60}</pagecontrol>
\t\t\t<onright>{lid + 60}</onright>
\t\t\t<visible>String.StartsWith(Window.Property(tikiskins.window_style),{style})</visible>
\t\t\t<itemlayout width="{LIST_W}" height="{ROW_H}">
{row(False)}
\t\t\t</itemlayout>
\t\t\t<focusedlayout width="{LIST_W}" height="{ROW_H}">
{row(True)}
\t\t\t</focusedlayout>
\t\t</control>
\t\t<include content="PP_Scrollbar">
\t\t\t<param name="id" value="{lid + 60}"/><param name="left" value="{LIST_LEFT + LIST_W + 18}"/>
\t\t\t<param name="top" value="{LIST_TOP}"/><param name="height" value="{ROW_H * ROWS}"/><param name="onleft" value="{lid}"/>
\t\t</include>"""


def page(crumb, title_label, meta_label, poster, plot=None):
    plot_xml = f"""
\t\t<control type="textbox">
\t\t\t<left>120</left><top>786</top><width>400</width><height>222</height>
\t\t\t<font>body_22</font><textcolor>body</textcolor>
\t\t\t<!-- static: no autoscroll; a long description stops at the box -->
\t\t\t<label>{plot}</label>
\t\t</control>""" if plot else ""
    return f"""\t\t<include>PP_Background</include>
\t\t<control type="label">
\t\t\t<left>120</left><top>56</top><width>1200</width><height>44</height><aligny>center</aligny>
\t\t\t<font>cap_20</font><textcolor>ink2</textcolor><label>Films  /  [COLOR ink]{X(crumb)}[/COLOR]</label>
\t\t</control>
\t\t<include>PP_Clock</include>
\t\t<include content="PP_Print">
\t\t\t<param name="left" value="120"/><param name="top" value="150"/>
\t\t\t<param name="width" value="400"/><param name="height" value="600"/>
\t\t\t<param name="art" value="{poster}"/>
\t\t\t<param name="title" value="{title_label}"/>
\t\t\t<param name="lift" value="true"/>
\t\t</include>{plot_xml}
\t\t<control type="label">
\t\t\t<left>{LIST_LEFT}</left><top>128</top><width>{LIST_W}</width><height>96</height><aligny>center</aligny>
\t\t\t<font>ttl_72</font><textcolor>ink</textcolor><label>{title_label}</label>
\t\t</control>
\t\t<control type="label">
\t\t\t<left>{LIST_LEFT}</left><top>230</top><width>{LIST_W}</width><height>32</height><aligny>center</aligny>
\t\t\t<font>cap_20</font><textcolor>ink2</textcolor><label>{meta_label}</label>
\t\t</control>
\t\t<control type="image"><left>{LIST_LEFT}</left><top>288</top><width>54</width><height>2</height><texture colordiffuse="ink">common/white.png</texture></control>"""


def main():
    W = "Window.Property"
    results = f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GENERATED by tools/make_pp_sources.py - edit that script, not this file.
	POV's source picker in Passe-partout's look (Kodi uses the skin's copy over POV's). -->
<window>
	<defaultcontrol always="true">2000</defaultcontrol>
	<include>Anim_DialogOpenClose</include>
	<controls>
{page("Choose a copy", f"$INFO[{W}(tikiskins.title)]",
      f"[COLOR ink]$INFO[{W}(tikiskins.total_results)] copies[/COLOR]$INFO[{W}(tikiskins.scrape_time),  ·  found in , s]  ·  best first",
      f"$INFO[{W}(tikiskins.poster)]", f"$INFO[{W}(tikiskins.plot)]")}
{results_list(2000, "list")}
{results_list(2001, "infolist")}
{results_list(2002, "widelist")}
\t\t<control type="label">
\t\t\t<left>{LIST_LEFT}</left><top>968</top><width>800</width><height>28</height><font>cap_20</font><textcolor>ink2</textcolor>
\t\t\t<label>The catalogue</label>
\t\t</control>
\t\t<control type="label">
\t\t\t<left>{LIST_LEFT}</left><top>998</top><width>800</width><height>28</height><font>cap_20</font><textcolor>ink</textcolor>
\t\t\t<label>Best first</label>
\t\t</control>
\t\t<control type="label">
\t\t\t<left>1300</left><top>990</top><width>500</width><height>36</height><align>right</align><font>mono_24</font><textcolor>ink2</textcolor>
\t\t\t<label>$INFO[Container(2000).CurrentItem]$INFO[Container(2000).NumItems, / ]</label>
\t\t\t<visible>Control.IsVisible(2000)</visible>
\t\t</control>
\t</controls>
</window>
"""
    P = "Window.Property(tikiskins.source_progress"
    buttons = f"""\t\t<control type="grouplist">
\t\t\t<left>{LIST_LEFT - 24}</left><top>780</top><width>1200</width><height>124</height>
\t\t\t<orientation>horizontal</orientation><itemgap>-36</itemgap>
\t\t\t<visible>String.IsEqual({P}.buttons),true)</visible>
\t\t\t<include content="PP_ButtonPrimary">
\t\t\t\t<param name="id" value="10"/><param name="label" value="$INFO[{P}.true_button)]"/>
\t\t\t</include>
\t\t\t<include content="PP_ButtonSecondary">
\t\t\t\t<param name="id" value="11"/><param name="label" value="$INFO[{P}.false_button)]"/>
\t\t\t</include>
\t\t</control>"""
    progress = f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GENERATED by tools/make_pp_sources.py - edit that script, not this file.
	POV's loading screen (and its questions, e.g. resume) in Passe-partout's look. -->
<window>
	<defaultcontrol always="true">10</defaultcontrol>
	<include>Anim_DialogOpenClose</include>
	<controls>
{page("Looking for copies", f"$INFO[{P}.title)]", f"$INFO[{P}.year)]", f"$INFO[{P}.poster)]")}
\t\t<control type="label">
\t\t\t<left>{LIST_LEFT}</left><top>350</top><width>{LIST_W}</width><height>60</height><aligny>center</aligny>
\t\t\t<font>ttl_44</font><textcolor>body</textcolor><label>Looking for copies…</label>
\t\t\t<visible>!String.IsEqual({P}.buttons),true)</visible>
\t\t</control>
\t\t<control type="progress" id="5000">
\t\t\t<left>{LIST_LEFT}</left><top>440</top><width>{LIST_W}</width><height>4</height>
\t\t\t<texturebg colordiffuse="rule_track">common/white.png</texturebg>
\t\t\t<midtexture colordiffuse="ink">common/white.png</midtexture>
\t\t\t<visible>!String.IsEqual({P}.buttons),true)</visible>
\t\t</control>
\t\t<!-- POV's own text (totals by quality, who is still looking); its colours come from POV's dialog highlight
\t\t     setting, set to the skin's ink -->
\t\t<control type="textbox" id="2000">
\t\t\t<left>{LIST_LEFT}</left><top>480</top><width>{LIST_W}</width><height>280</height>
\t\t\t<font>body_26</font><textcolor>body</textcolor>
\t\t</control>
{buttons}
\t</controls>
</window>
"""
    includes = f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GENERATED by tools/make_pp_sources.py - edit that script, not this file. Badge columns of the source picker. -->
<includes>
{variables()}
</includes>
"""
    (OUT / "sources_results.xml").write_text(results)
    (OUT / "progress_media.xml").write_text(progress)
    (OUT / "Includes_PovSources.xml").write_text(includes)
    print("wrote sources_results.xml, progress_media.xml, Includes_PovSources.xml")


if __name__ == "__main__":
    main()
