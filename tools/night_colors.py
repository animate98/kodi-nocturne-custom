#!/usr/bin/env python3
"""Passe-partout Custom night mode: route the skin's named colours through $VAR[C_<name>].

Kodi colour themes need a skin reload to switch (and a reload while Python runs crashes Kodi 22 RC), so the
skin's colours are variables instead: C_ink = n_ink when Skin.HasSetting(pp.night), else ink
(colors/defaults.xml holds both sets). This rewrites every use of a named colour - colordiffuse, *color tags,
colour params, variable values and [COLOR x] label markup - in the skin XML and in the generators in tools/,
and writes the C_* variables to 1080i/Includes_Night.xml. Safe to run again (already-converted uses are left).

The placard textures are a dark fill over a soft shadow, and a colordiffuse can only darken - and Kodi buttons
take no variables in texture paths. So the tool bakes media/pp/<name>_w.png (white fill, black shadow) and
the skin tints them with $VAR[C_placard]: dark ink by day, light ink by night. Needs Pillow for the textures
(pip install pillow); without it the XML part still runs.

  python3 tools/night_colors.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIN = ROOT / "skin.passepartout.custom"
KEEP = {"white", "black", "clear"}          # the same by day and night
NIGHT = "Skin.HasSetting(pp.night)"
PLACARDS = ["placard_btn_key", "placard_btn", "placard_btn56", "placard_key"]
DAY_FILL, DAY_SHADOW = (28, 27, 25), (60, 46, 32)
WHITE_FILL, BLACK_SHADOW = (255, 255, 255), (0, 0, 0)


def names():
    text = (SKIN / "colors/defaults.xml").read_text()
    all_ = re.findall(r'<color name="([a-z_0-9]+)"', text)
    return [n for n in all_ if not n.startswith("n_") and n not in KEEP]


def convert(text, ns):
    alt = "|".join(sorted(ns, key=len, reverse=True))
    v = lambda n: f"$VAR[C_{n}]"
    text = re.sub(rf'colordiffuse="({alt})"', lambda m: f'colordiffuse="{v(m[1])}"', text)
    text = re.sub(rf'<(textcolor|focusedcolor|disabledcolor|selectedcolor|shadowcolor|invalidcolor)>({alt})</',
                  lambda m: f"<{m[1]}>{v(m[2])}</", text)
    text = re.sub(rf'(<param name="[a-z_0-9]+" value=")({alt})("\s*/>)', lambda m: m[1] + v(m[2]) + m[3], text)
    text = re.sub(rf'(<param name="[a-z_0-9]+">)({alt})(</param>)', lambda m: m[1] + v(m[2]) + m[3], text)
    text = re.sub(rf'(<value(?: condition="[^"]*")?>)({alt})(</value>)', lambda m: m[1] + v(m[2]) + m[3], text)
    text = re.sub(rf'\[COLOR ({alt})\]', lambda m: f"[COLOR {v(m[1])}]", text)
    text = re.sub(rf'(<texture[a-z]*(?: border="[^"]*")?)>pp/({"|".join(PLACARDS)})\.png<',
                  lambda m: f'{m[1]} colordiffuse="$VAR[C_placard]">pp/{m[2]}_w.png<', text)
    text = re.sub(r'<texture( border="[^"]*")?>pp/bevel\.png<', lambda m: f'<texture{m[1] or ""} colordiffuse="$VAR[C_bevel]">pp/bevel.png<', text)
    return text


def bake_textures():
    try:
        from PIL import Image
    except ImportError:
        print("Pillow missing: white placards not rebuilt")
        return
    span = [f - s for f, s in zip(DAY_FILL, DAY_SHADOW)]
    for name in PLACARDS:
        im = Image.open(SKIN / f"media/pp/{name}.png").convert("RGBA")
        px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, a = px[x, y]
                # where this pixel sits between the shadow colour (0) and the fill (1)
                t = sum((c - s) * d for c, s, d in zip((r, g, b), DAY_SHADOW, span)) / sum(d * d for d in span)
                t = min(1.0, max(0.0, t))
                px[x, y] = tuple(round(s + t * (f - s)) for s, f in zip(BLACK_SHADOW, WHITE_FILL)) + (a,)
        im.save(SKIN / f"media/pp/{name}_w.png", optimize=True)
        print("baked", f"media/pp/{name}_w.png")


def main():
    ns = names()
    files = sorted((SKIN / "1080i").glob("*.xml")) + [ROOT / f"tools/{p}" for p in
                                                        ("make_pp_film_rows.py", "make_pp_grid.py", "make_pp_sources.py")]
    for f in files:
        if f.name == "Includes_Night.xml":
            continue
        old = f.read_text(encoding="utf-8")
        new = convert(old, ns)
        if new != old:
            f.write_text(new, encoding="utf-8")
            print("converted", f.relative_to(ROOT))
    bake_textures()
    body = "\n".join(f'\t<variable name="C_{n}">\n\t\t<value condition="{NIGHT}">n_{n}</value>\n\t\t<value>{n}</value>\n\t</variable>'
                     for n in ns)
    (SKIN / "1080i/Includes_Night.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<!-- Night mode colour switch, written by tools/night_colors.py -->\n'
        f"<includes>\n{body}\n</includes>\n", encoding="utf-8")


if __name__ == "__main__":
    main()
