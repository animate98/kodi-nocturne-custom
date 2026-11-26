#!/usr/bin/env python3
"""Generate 1080i/Includes_PovRows.xml: the POV sections on the Home Films tab.

One section per screen. Left / Right at the edge of a section moves to the previous / next one; VIEW ALL
(bottom left) opens the whole list in the Corridor view; OK on a poster opens its info page.

Layout rules (from the Figma mockup, 2026-11-26):
  1. vertical 2:3 posters only; 3, 5 or 7 per section, as big as the canvas allows;
  2. one consistent GAP between posters, horizontally and vertically;
     columns hang near the top so the upper half of the canvas is never empty (at most one column drops lower);
  3. every section has its own layout, generated from a fixed per-section seed (re-roll = change SEED_SALT
     or the section's seed);
  4. posters stay inside the canvas: not in the caption band, the arrow columns, or the VIEW ALL corner;
  5. arrows at the sides show that Left / Right go to the previous / next section.

A layout is a row of columns. Each column has its own poster width, holds 1-3 posters stacked with GAP, and
hangs at its own height. The #1 title gets the biggest poster.

The POV lists are fetched by hidden containers ONE AT A TIME (Kodi 22 RC's Python segfaults when several
plugin calls start together): each container becomes visible (= fetches) after the previous one has loaded.

Run from the repo root:  python3 tools/make_pov_rows.py
"""
import random
from pathlib import Path
from xml.sax.saxutils import escape as X

OUT = Path(__file__).resolve().parent.parent / "skin.nocturne.custom/1080i/Includes_PovRows.xml"
POV = "plugin://plugin.video.pov/"

# ---- screen geometry (1920 x 1080) ------------------------------------------------------------------
PAGE_W = 1920
CAPTION_Y, CAPTION_H = 148, 36           # section name (left) / highlighted title (right)
CANVAS = (157, 210, 1756, 1046)          # x0, y0, x1, y1 the posters may use (arrow columns outside)
NO_GO = (0, 846, 520, 1080)              # the VIEW ALL corner: posters stay out
BUTTON = (98, 940, 322, 64)              # VIEW ALL x, y, w, h
RESUME = (98, 862, 322, 64)              # RESUME (On the easel only), above VIEW ALL
RESUME_SECTIONS = {"On the easel"}       # resume = play item #1 (the latest in progress) through POV
GAP = 64
MIN_W, MAX_W = 210, 540                  # poster widths (height = 1.5 x width)
POSTERS = (3, 5, 7)                      # allowed posters per section
SEED_SALT = "nocturne-1"

TORCH_REST = (930, 526)                  # the torch's resting centre (films b3)
WORD = 9001                              # the Films word on the cornice
ID_BASE = 9600                           # poster j of section g = ID_BASE + 10*g + j; VIEW ALL = +9


def mlist(action):
    return f"{POV}?mode=build_movie_list&action={action}"


# (title, meta, view-all url, has data list, cards [(label, url)] when there is no data list)
FILMS = [
    ("On the easel", "continue watching", mlist("in_progress_movies"), True, None),
    ("Trending this week", "TMDb", mlist("tmdb_movies_trending"), True, None),
    ("Popular", "TMDb", mlist("tmdb_movies_popular"), True, None),
    ("Latest releases", "digital & disc", mlist("tmdb_movies_latest_releases"), True, None),
    ("In cinemas", "premieres", mlist("tmdb_movies_premieres"), True, None),
    ("Coming soon", "upcoming", mlist("tmdb_movies_upcoming"), True, None),
    ("Blockbusters", "TMDb", mlist("tmdb_movies_blockbusters"), True, None),
    ("Trending on Trakt", "Trakt", mlist("trakt_movies_trending"), True, None),
    ("Most watched", "Trakt", mlist("trakt_movies_most_watched"), True, None),
    ("Oscar winners", "best picture", mlist("tmdb_oscar_winners"), True, None),
    ("Watched", "your history", mlist("watched_movies"), True, None),
    ("Browse", "genres & years", f"{POV}?mode=navigator.main&action=MovieList", False,
     [("Genres", f"{POV}?mode=navigator.genres&menu_type=movie"),
      ("Years", f"{POV}?mode=navigator.years&menu_type=movie")]),
]
MAY_BE_EMPTY = {"On the easel", "Watched"}   # load last in the chain, never block it
CHAIN_AFTER = 9213                           # start once the Series wall lists are in
DATA_BASE = 9401
SEC = "films"
SECTION_VIS = (f"[String.IsEqual(Window(Home).Property(nocturne.section),{SEC}) | "
               "String.IsEmpty(Window(Home).Property(nocturne.section))] + !Skin.HasSetting(HideMenu.Movies) "
               "+ !$EXP[CustomRowsFocus]")


def fid(g, j):
    return ID_BASE + 10 * g + j


def bid(g):
    return ID_BASE + 10 * g + 9


# ---- layout generator --------------------------------------------------------------------------------
def overlaps(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


TOP_HALF_COVER = 0.8                     # share of the layout's width that must reach into the top half


def gen_layout(name, used, count=None):
    """Columns of 2:3 posters. Returns [(x, y, w, h)] in screen coords, biggest first."""
    rnd = random.Random(f"{SEED_SALT}:{name}")
    cx0, cy0, cx1, cy1 = CANVAS
    avail_w, avail_h = cx1 - cx0, cy1 - cy0
    no_go = (NO_GO[0], NO_GO[1] - GAP, NO_GO[2] - NO_GO[0] + GAP, NO_GO[3] - NO_GO[1] + GAP)
    for _ in range(200000):
        ncol = rnd.randint(2, 5)
        stacks = [rnd.choice((1, 1, 2)) for _ in range(ncol)]       # at most two posters per column
        if sum(stacks) not in (count or POSTERS):
            continue
        raw = [rnd.uniform(0.7, 1.6) / (0.6 + 0.4 * s) for s in stacks]       # stacked columns run narrower
        target = rnd.uniform(0.82, 1.0) * avail_w
        k = (target - GAP * (ncol - 1)) / sum(raw)
        widths = [round(r * k) for r in raw]
        if min(widths) < MIN_W or max(widths) > MAX_W:
            continue
        heights = [s * round(1.5 * w) + (s - 1) * GAP for s, w in zip(stacks, widths)]
        if max(heights) > avail_h:
            continue
        used_w = sum(widths) + GAP * (ncol - 1)
        x = cx0 + (avail_w - used_w) // 2
        rects, ok = [], True
        drop = rnd.randrange(ncol) if rnd.random() < 0.5 else -1     # the one column allowed to hang lower
        for ci, (s, w, colh) in enumerate(zip(stacks, widths, heights)):
            room = avail_h - colh
            reach = room * 0.6 if ci == drop else min(room, 0.15 * avail_h)
            yoff = round(rnd.uniform(0, reach) / 10) * 10
            col = []
            for i in range(s):
                h = round(1.5 * w)
                col.append((x, cy0 + yoff + i * (h + GAP), w, h))
            if any(overlaps(r, no_go) for r in col):
                # slide the column up just enough, if it can
                bottom = max(r[1] + r[3] for r in col)
                lift = bottom - no_go[1]
                if col[0][1] - lift < cy0:
                    ok = False
                    break
                col = [(rx, ry - lift, rw, rh) for rx, ry, rw, rh in col]
            rects += col
            x += w + GAP
        if not ok:
            continue
        # two layouts may share a column pattern only if the big poster hangs in a different column
        sig = (tuple(stacks), widths.index(max(widths)))
        if sig in used:
            continue
        mid = cy0 + avail_h / 2
        top_w = sum(w for (x_, y_, w, h_) in rects if y_ < mid)
        if top_w < TOP_HALF_COVER * sum(widths):
            continue
        used.add(sig)
        rects.sort(key=lambda r: (-r[2], r[0], r[1]))     # biggest first -> item #1
        return rects
    raise SystemExit(f"no layout found for {name}")


# ---- navigation (geometric) ----------------------------------------------------------------------------
def centre(r):
    return r[0] + r[2] / 2, r[1] + r[3] / 2


def neighbour(rects, j, direction):
    cx, cy = centre(rects[j])
    best, best_score = None, None
    for i, r in enumerate(rects):
        if i == j:
            continue
        x, y = centre(r)
        dx, dy = x - cx, y - cy
        if direction == "left" and dx < -5:
            score = -dx + 2.5 * abs(dy)
        elif direction == "right" and dx > 5:
            score = dx + 2.5 * abs(dy)
        elif direction == "up" and r[1] + r[3] <= rects[j][1]:
            score = -dy + 2 * abs(dx)
        elif direction == "down" and r[1] >= rects[j][1] + rects[j][3]:
            score = dy + 2 * abs(dx)
        else:
            continue
        if best_score is None or score < best_score:
            best, best_score = i, score
    return best


def entry(rects, side):
    """The poster you land on when entering a section from the left / right edge."""
    if side == "left":
        return min(range(len(rects)), key=lambda i: (rects[i][0], rects[i][1]))
    return max(range(len(rects)), key=lambda i: (rects[i][0] + rects[i][2], -rects[i][1]))


def main():
    n = len(FILMS)
    cids, nid = {}, DATA_BASE
    for g, e in enumerate(FILMS):
        if e[3]:
            cids[g] = nid
            nid += 1

    used = set()
    layouts = []
    for g, (title, *_rest) in enumerate(FILMS):
        if g in cids:
            layouts.append(gen_layout(title, used, (3, 5) if title == "On the easel" else None))
        else:   # browse cards: two big posters-shaped cards
            w = 360
            h = 540
            x0 = (CANVAS[0] + CANVAS[2]) // 2 - w - GAP // 2
            layouts.append([(x0, 290, w, h), (x0 + w + GAP, 290, w, h)])

    # ---------- hidden data containers, loaded one at a time ----------
    data = []
    order = sorted(cids, key=lambda g: FILMS[g][0] in MAY_BE_EMPTY)
    prev, prev_empty = CHAIN_AFTER, False
    for g in order:
        ready = (f"Control.IsVisible({prev}) + !Container({prev}).IsUpdating" if prev_empty
                 else f"Integer.IsGreater(Container({prev}).NumItems,0)")
        data.append(f"""\t\t<control type="list" id="{cids[g]}">
\t\t\t<visible>{ready}</visible>
\t\t\t<left>0</left><top>0</top><width>5</width><height>1</height>
\t\t\t<orientation>horizontal</orientation>
\t\t\t<itemlayout width="1" height="1"/><focusedlayout width="1" height="1"/>
\t\t\t<content target="videos">{X(FILMS[g][2])}</content>
\t\t</control>""")
        prev, prev_empty = cids[g], FILMS[g][0] in MAY_BE_EMPTY

    # ---------- variables ----------
    vars_ = []
    for g, cid in cids.items():
        for k in range(len(layouts[g])):
            vals = []
            for a in ("poster", "thumb", "fanart"):
                li = f"Container({cid}).ListItemAbsolute({k}).Art({a})"
                vals.append(f'\t\t<value condition="!String.IsEmpty({li})">$INFO[{li}]</value>')
            vars_.append(f'\t<variable name="Pov_{cid}_p{k}">\n' + "\n".join(vals) + "\n\t</variable>")
    for g, e in enumerate(FILMS):
        vals = []
        for j in range(len(layouts[g])):
            if g in cids:
                li = f"Container({cids[g]}).ListItemAbsolute({j})"
                lab = f"$INFO[{li}.Label]$INFO[{li}.Year,  ·  ,]"
            else:
                lab = X(e[4][j][0])
            vals.append(f'\t\t<value condition="Control.HasFocus({fid(g, j)})">{lab}</value>')
        vals.append(f'\t\t<value condition="Control.HasFocus({bid(g)})">{X(e[1])}</value>')
        if g in cids and e[0] in RESUME_SECTIONS:
            li = f"Container({cids[g]}).ListItemAbsolute(0)"
            vals.append(f'\t\t<value condition="Control.HasFocus({ID_BASE + 10 * g + 8})">Resume  $INFO[{li}.Label]</value>')
        vars_.append(f'\t<variable name="Pov_{SEC}_focus{g}">\n' + "\n".join(vals) + "\n\t</variable>")

    # ---------- navigation helpers ----------
    def exists(g, j):
        return "true" if g not in cids else f"!String.IsEmpty(Container({cids[g]}).ListItemAbsolute({j}).Label)"

    def to_poster(tag, g, j):
        ex = exists(g, j)
        if ex == "true":
            return [f"<{tag}>{fid(g, j)}</{tag}>"]
        return [f'<{tag} condition="{ex}">{fid(g, j)}</{tag}>', f'<{tag} condition="!{ex}">{bid(g)}</{tag}>']

    # ---------- pages ----------
    pages = []
    for g, (title, meta, url, _, cards) in enumerate(FILMS):
        rects = layouts[g]
        lit_any = "[" + " | ".join([f"Control.HasFocus({fid(g, j)})" for j in range(len(rects))]
                                   + [f"Control.HasFocus({bid(g)})", f"Control.HasFocus({ID_BASE + 10 * g + 8})"]) + "]"
        prev_name = FILMS[g - 1][0] if g > 0 else ""
        next_name = FILMS[g + 1][0] if g < n - 1 else ""
        p = [f"""\t\t\t<!-- section {g}: {X(title)} -->
\t\t\t<control type="group">
\t\t\t\t<left>{PAGE_W * g}</left><top>0</top><width>{PAGE_W}</width><height>1080</height>
\t\t\t\t<control type="label">
\t\t\t\t\t<left>40</left><top>{CAPTION_Y}</top><width>900</width><height>{CAPTION_H}</height><aligny>center</aligny>
\t\t\t\t\t<font>caps_22</font><textcolor>caption_lit</textcolor><shadowcolor>b3000000</shadowcolor>
\t\t\t\t\t<label>{X(title)}</label>
\t\t\t\t</control>
\t\t\t\t<control type="label">
\t\t\t\t\t<left>940</left><top>{CAPTION_Y}</top><width>940</width><height>{CAPTION_H}</height>
\t\t\t\t\t<align>right</align><aligny>center</aligny>
\t\t\t\t\t<font>body_24</font><textcolor>text_primary</textcolor><shadowcolor>b3000000</shadowcolor>
\t\t\t\t\t<label>$VAR[Pov_{SEC}_focus{g}]</label>
\t\t\t\t\t<visible>{lit_any}</visible>
\t\t\t\t</control>"""]
        for side, name in (("l", prev_name), ("r", next_name)):
            if not name:
                continue
            ax = 42 if side == "l" else PAGE_W - 42 - 36
            p.append(f"""\t\t\t\t<control type="image">
\t\t\t\t\t<left>{ax}</left><top>496</top><width>36</width><height>60</height>
\t\t\t\t\t<texture flipx="{'true' if side == 'l' else 'false'}" colordiffuse="caption_lit">icons/chevron_right.png</texture>
\t\t\t\t\t<aspectratio>keep</aspectratio>
\t\t\t\t</control>""")
        if g in cids and title in MAY_BE_EMPTY:
            p.append(f"""\t\t\t\t<control type="label">
\t\t\t\t\t<left>560</left><top>440</top><width>800</width><height>160</height>
\t\t\t\t\t<align>center</align><aligny>center</aligny><wrapmultiline>true</wrapmultiline>
\t\t\t\t\t<font>body_26</font><textcolor>text_tertiary</textcolor>
\t\t\t\t\t<label>Nothing here yet.[CR]Start a film and it will hang here.</label>
\t\t\t\t\t<visible>String.IsEmpty(Container({cids[g]}).ListItemAbsolute(0).Label)</visible>
\t\t\t\t</control>""")
        for j, (x, y, w, h) in enumerate(rects):
            if g in cids:
                art = f"$VAR[Pov_{cids[g]}_p{j}]"
                label = f"$INFO[Container({cids[g]}).ListItemAbsolute({j}).Label]"
                click = [f"SetFocus({cids[g]},{j},absolute)", "Action(Info)", f"SetFocus({fid(g, j)})"]
            else:
                art, label = "", X(cards[j][0])
                click = [f"SetProperty(nocturne.povreturn,{fid(g, j)},home)",
                         f'ActivateWindow(Videos,"{X(cards[j][1])}",return)']
            nav = []
            l, r_, u, d = (neighbour(rects, j, s) for s in ("left", "right", "up", "down"))
            if l is not None:
                nav += to_poster("onleft", g, l)
            elif g > 0:
                nav += to_poster("onleft", g - 1, entry(layouts[g - 1], "right"))
            if r_ is not None:
                nav += to_poster("onright", g, r_)
            elif g < n - 1:
                nav += to_poster("onright", g + 1, entry(layouts[g + 1], "left"))
            nav += to_poster("onup", g, u) if u is not None else [f"<onup>{WORD}</onup>"]
            nav += to_poster("ondown", g, d) if d is not None else [f"<ondown>{bid(g)}</ondown>"]
            p.append(f"""\t\t\t\t<control type="group">
\t\t\t\t\t<left>{x}</left><top>{y}</top><width>{w}</width><height>{h}</height>
\t\t\t\t\t<visible>{exists(g, j)}</visible>
\t\t\t\t\t<include content="Noc_FrameParts">
\t\t\t\t\t\t<param name="art" value="{art}"/>
\t\t\t\t\t\t<param name="lit" value="Control.HasFocus({fid(g, j)})"/>
\t\t\t\t\t\t<param name="label" value="{label}"/>
\t\t\t\t\t</include>
\t\t\t\t</control>
\t\t\t\t<control type="button" id="{fid(g, j)}">
\t\t\t\t\t<left>{x}</left><top>{y}</top><width>{w}</width><height>{h}</height>
\t\t\t\t\t<texturefocus/><texturenofocus/><label/>
\t\t\t\t\t<visible>{exists(g, j)}</visible>
\t\t\t\t\t<onfocus>SetProperty(nocturne.slot,pv_{g}_{j},home)</onfocus>
\t\t\t\t\t<onfocus>SetProperty(nocturne.povg,{g},home)</onfocus>
""" + "".join(f"\t\t\t\t\t<onclick>{c}</onclick>\n" for c in click)
                + "".join(f"\t\t\t\t\t{t}\n" for t in nav)
                + f"\t\t\t\t\t<onback>{WORD}</onback>\n\t\t\t\t</control>")
        # VIEW ALL: Up = the poster nearest the button
        bx, by, bw, bh = BUTTON
        near = min(range(len(rects)), key=lambda i: abs(centre(rects[i])[0] - (bx + bw / 2))
                   + abs(rects[i][1] + rects[i][3] - by))
        has_resume = g in cids and title in RESUME_SECTIONS
        if has_resume:
            rid = ID_BASE + 10 * g + 8
            ex0 = exists(g, 0)
            bnav = [f'<onup condition="{ex0}">{rid}</onup>'] + [t.replace('<onup', f'<onup condition="!{ex0}"', 1)
                                                               if 'condition' not in t else t
                                                               for t in to_poster("onup", g, near)]
            rx, ry, rw, rh = RESUME
            item = f"Container({cids[g]}).ListItemAbsolute(0)"
            p.append(f"""\t\t\t\t<control type="button" id="{rid}">
\t\t\t\t\t<left>{rx}</left><top>{ry}</top><width>{rw}</width><height>{rh}</height>
\t\t\t\t\t<label>Resume  ›</label>
\t\t\t\t\t<font>caps_20</font><align>center</align><aligny>center</aligny>
\t\t\t\t\t<textcolor>text_secondary</textcolor><focusedcolor>ink</focusedcolor>
\t\t\t\t\t<texturenofocus border="26,0,26,0" colordiffuse="40ffffff">noc/plaque2.png</texturenofocus>
\t\t\t\t\t<texturefocus border="26,0,26,0">noc/plaque2.png</texturefocus>
\t\t\t\t\t<visible>{ex0}</visible>
\t\t\t\t\t<onfocus>SetProperty(nocturne.slot,pv_{g}_r,home)</onfocus>
\t\t\t\t\t<onfocus>SetProperty(nocturne.povg,{g},home)</onfocus>
\t\t\t\t\t<onclick>RunPlugin(&quot;$INFO[{item}.FileNameAndPath]&quot;)</onclick>
""" + "".join(f"\t\t\t\t\t{t}\n" for t in to_poster("onup", g, near))
                + f"\t\t\t\t\t<ondown>{bid(g)}</ondown>\n\t\t\t\t\t<onback>{WORD}</onback>\n\t\t\t\t</control>")
        else:
            bnav = to_poster("onup", g, near)
        if g > 0:
            bnav.append(f"<onleft>{bid(g - 1)}</onleft>")
        if g < n - 1:
            bnav.append(f"<onright>{bid(g + 1)}</onright>")
        p.append(f"""\t\t\t\t<control type="button" id="{bid(g)}">
\t\t\t\t\t<left>{bx}</left><top>{by}</top><width>{bw}</width><height>{bh}</height>
\t\t\t\t\t<label>View all  ›</label>
\t\t\t\t\t<font>caps_20</font><align>center</align><aligny>center</aligny>
\t\t\t\t\t<textcolor>text_secondary</textcolor><focusedcolor>ink</focusedcolor>
\t\t\t\t\t<texturenofocus border="26,0,26,0" colordiffuse="40ffffff">noc/plaque2.png</texturenofocus>
\t\t\t\t\t<texturefocus border="26,0,26,0">noc/plaque2.png</texturefocus>
\t\t\t\t\t<onfocus>SetProperty(nocturne.slot,pv_{g}_b,home)</onfocus>
\t\t\t\t\t<onfocus>SetProperty(nocturne.povg,{g},home)</onfocus>
\t\t\t\t\t<onclick>SetProperty(nocturne.povreturn,{bid(g)},home)</onclick>
\t\t\t\t\t<onclick>ActivateWindow(Videos,"{X(url)}",return)</onclick>
""" + "".join(f"\t\t\t\t\t{t}\n" for t in bnav)
            + f"\t\t\t\t\t<onback>{WORD}</onback>\n\t\t\t\t</control>\n\t\t\t</control>")
        pages.append("\n".join(p))

    strip_anims = [
        f'\t\t\t<animation effect="slide" start="0,0" end="{-PAGE_W * g},0" time="360" tween="sine" '
        f'easing="inout" condition="String.IsEqual(Window(Home).Property(nocturne.povg),{g})">Conditional</animation>'
        for g in range(1, n)]
    row = f"""\t<include name="Home_PovRow_{SEC}">
\t<control type="group">
\t\t<visible>{SECTION_VIS}</visible>
\t\t<include>Anim_SectionSwap</include>
\t\t<control type="group">
{chr(10).join(strip_anims)}
{chr(10).join(pages)}
\t\t</control>
\t</control>
\t</include>"""

    # ---------- Films word: Down lands in the section you were last in ----------
    downs = []
    for g in range(n):
        cond = f"String.IsEqual(Window(Home).Property(nocturne.povg),{g})"
        if g == 0:
            cond = f"[{cond} | String.IsEmpty(Window(Home).Property(nocturne.povg))]"
        j = entry(layouts[g], "left")
        ex = exists(g, j)
        if ex == "true":
            downs.append(f'\t\t<ondown condition="{cond}">{fid(g, j)}</ondown>')
        else:
            downs.append(f'\t\t<ondown condition="{cond} + {ex}">{fid(g, j)}</ondown>')
            downs.append(f'\t\t<ondown condition="{cond} + !{ex}">{bid(g)}</ondown>')
    word_down = f"\t<include name=\"Home_PovWordDown_{SEC}\">\n" + "\n".join(downs) + "\n\t</include>"

    # ---------- torch: page-relative positions (the focused page is always on screen) ----------
    def torch(instant):
        t = 1 if instant else 220
        out = []
        for g, rects in enumerate(layouts):
            pts = [(j, *centre(r)) for j, r in enumerate(rects)]
            pts.append(("b", BUTTON[0] + BUTTON[2] / 2, BUTTON[1] + BUTTON[3] / 2))
            pts.append(("r", RESUME[0] + RESUME[2] / 2, RESUME[1] + RESUME[3] / 2))
            for j, cx, cy in pts:
                dx, dy = round(cx - TORCH_REST[0]), round(cy - TORCH_REST[1])
                out.append(f'\t\t<animation effect="slide" start="0,0" end="{dx},{dy}" time="{t}" tween="sine" '
                           f'easing="inout" condition="String.IsEqual(Window(Home).Property(nocturne.slot),'
                           f'pv_{g}_{j})">Conditional</animation>')
        return "\n".join(out)

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GENERATED by tools/make_pov_rows.py - edit that script, not this file. -->
<includes>
{chr(10).join(vars_)}
\t<include name="Home_PovData">
{chr(10).join(data)}
\t</include>
{row}
{word_down}
\t<include name="Home_PovTorchNormal">
{torch(False)}
\t</include>
\t<include name="Home_PovTorchReduced">
{torch(True)}
\t</include>
</includes>
"""
    OUT.write_text(xml)
    print(f"wrote {OUT.name}: {n} sections, {sum(map(len, layouts))} posters, {len(cids)} data lists")
    return layouts


if __name__ == "__main__":
    main()
