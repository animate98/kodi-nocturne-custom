#!/usr/bin/env python3
"""Build the Kodi repository that GitHub Pages serves (run by .github/workflows/publish.yml).

  dist/
    addons.xml, addons.xml.md5
    index.html                                   (Kodi can browse it as a file source)
    repository.nocturne.custom-<ver>.zip          (install this once: "Install from zip file")
    <addon id>/<addon id>-<ver>.zip              (what Kodi downloads to install / update)

The skin's version is rewritten to MAJOR.MINOR.<BUILD_NUMBER> so every push is a newer release.

Usage: BUILD_NUMBER=42 python3 tools/build_repo.py
"""
import hashlib
import os
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
ADDONS = ["skin.nocturne.custom", "repository.nocturne.custom"]
SKIP = {".DS_Store"}
VERSION_RE = re.compile(r'(<addon\b[^>]*\bversion=")([^"]+)(")')


def addon_xml(addon, build):
    text = (ROOT / addon / "addon.xml").read_text(encoding="utf-8")
    if addon.startswith("skin.") and build:
        base = VERSION_RE.search(text).group(2).split(".")
        text = VERSION_RE.sub(lambda m: f"{m.group(1)}{base[0]}.{base[1]}.{build}{m.group(3)}", text, count=1)
    return text, VERSION_RE.search(text).group(2)


def zip_addon(addon, text, version):
    out = DIST / addon / f"{addon}-{version}.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted((ROOT / addon).rglob("*")):
            if path.is_dir() or path.name in SKIP:
                continue
            rel = path.relative_to(ROOT)
            if rel.as_posix() == f"{addon}/addon.xml":
                z.writestr(rel.as_posix(), text)
            else:
                z.write(path, rel.as_posix())
    return out


def main():
    build = os.environ.get("BUILD_NUMBER", "")
    shutil.rmtree(DIST, ignore_errors=True)
    DIST.mkdir()
    entries, links = [], []
    for addon in ADDONS:
        text, version = addon_xml(addon, build)
        out = zip_addon(addon, text, version)
        for asset in ("icon.png", "resources/icon.png", "resources/fanart.jpg"):
            src = ROOT / addon / asset
            if src.exists():
                shutil.copy(src, out.parent / Path(asset).name)
        entries.append(re.sub(r"^<\?xml[^>]*\?>\s*", "", text).strip())
        links.append(f"{addon}/")
        if addon.startswith("repository."):
            shutil.copy(out, DIST / out.name)
            links.insert(0, out.name)
        print(f"{addon} {version}")
    addons = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n' + "\n".join(entries) + "\n</addons>\n"
    (DIST / "addons.xml").write_text(addons, encoding="utf-8")
    (DIST / "addons.xml.md5").write_text(hashlib.md5(addons.encode("utf-8")).hexdigest(), encoding="utf-8")
    (DIST / "index.html").write_text(
        "<!doctype html><html><body>\n" + "\n".join(f'<a href="{l}">{l}</a><br>' for l in links) + "\n</body></html>\n")
    for addon in ADDONS:
        files = sorted(p.name for p in (DIST / addon).iterdir())
        (DIST / addon / "index.html").write_text(
            "<!doctype html><html><body>\n" + "\n".join(f'<a href="{f}">{f}</a><br>' for f in files) + "\n</body></html>\n")


if __name__ == "__main__":
    main()
