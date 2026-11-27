#!/usr/bin/env python3
"""Logo badges for the source picker, for this box only (not published).

Fetches the badge images used by skin.passepartout.custom's source picker from the "nuvio-minimalist-badges"
pack (github.com/sweatycab/nuvio-minimalist-badges, white set), converts them to PNG with macOS's sips (Kodi
can't draw SVG) and writes them to local/badges/ - git-ignored: the pack has no licence and the marks are
Dolby's / IMAX's / DTS's, so they stay off GitHub and the Kodi repository.

Install on the box (they are drawn when Skin setting pp.logobadges is on; without it, text badges):
  python3 tools/make_badges.py
  rsync -a local/badges/ root@<box>:/storage/.kodi/userdata/addon_data/skin.passepartout.custom/badges/
"""
import subprocess
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "local/badges"
BASE = "https://cdn.jsdelivr.net/gh/sweatycab/nuvio-minimalist-badges@main/badges/"
HEIGHT = 88   # 4x the 22 px they are drawn at on the 1080 layout (sharp on 4K)

# skin file name -> pack file name (tools/make_pp_sources.py BADGES)
FILES = {
    "dv": "white-DV", "hdr10plus": "white-HDR10Plus", "hdr": "white-HDR", "sdr": "white-SDR",
    "imax": "white-IMAX", "imax-enhanced": "white-IMAX-enhanced", "10bit": "white-10bit",
    "remux": "white-remux", "bluray": "white-bluray", "webdl": "white-webdl", "webrip": "white-webrip",
    "hdtv": "white-HDTV", "dvdrip": "white-DVDRip",
    "hevc": "white-HEVC", "h264": "white-H264", "av1": "white-AV1", "xvid": "white-XviD",
    "atmos": "white-Atmos", "truehd": "white-TrueHD", "dtsx": "white-dtsx", "dtshdma": "white-dtshdma",
    "dtshd": "white-dtshd", "dts": "white-dts", "ddplus": "white-DDPLUS", "dd": "white-DD",
    "71": "white-71", "61": "white-61", "51": "white-51",
}


def size_of(svg):
    import re
    w = re.search(r'<svg[^>]*\bwidth="([\d.]+)', svg)
    h = re.search(r'<svg[^>]*\bheight="([\d.]+)', svg)
    return float(w.group(1)), float(h.group(1))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for name, src in FILES.items():
            svg_path = Path(tmp) / f"{src}.svg"
            with urllib.request.urlopen(BASE + src + ".svg", timeout=30) as r:
                svg_path.write_bytes(r.read())
            w, h = size_of(svg_path.read_text())
            width = round(w * HEIGHT / h)
            png = OUT / f"{name}.png"
            subprocess.run(["sips", "-s", "format", "png", "-z", str(HEIGHT), str(width), str(svg_path),
                            "--out", str(png)], check=True, capture_output=True)
            print(f"{name:14} {width}x{HEIGHT}")


if __name__ == "__main__":
    main()
