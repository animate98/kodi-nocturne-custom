# Nocturne Custom & Passe-partout Custom

A personal Kodi skin for CoreELEC (Kodi 22), forked from
[Nocturne](https://github.com/KarmaMole/kodi-skins) v0.9.19 by KarmaMole.
Licensed under GPL-2.0-or-later, same as the original (see `skin.nocturne.custom/LICENSE.txt`).

## Passe-partout Custom

`skin.passepartout.custom/` is Passe-partout 0.9.22 by KarmaMole with POV in place of the Kodi library: Home's
exhibition / Continue watching / the rest of the room, the Films and Series words (POV menus) and Search all come
from POV; Music is hidden. OK opens Kodi's info page, its Play runs POV, Back stops playback (same pieces as below).

## Layout

- `skin.nocturne.custom/` – the skin add-on itself (installed to `/storage/.kodi/addons/` on the box)
  - `colors/defaults.xml` – color palette
  - `1080i/` – window and include XML
  - `media/` – textures
- `tools/make_pov_rows.py` – generates `1080i/Includes_PovRows.xml`, the POV sections on the Films tab
  (layout rules, lists and seeds are at the top of the script)
- `skin.nocturne.custom/keymaps/nocturne_ok.xml` – OK opens Kodi's info page in video lists; Back stops playback
  (the skin installs it itself via `Timers.xml` → `scripts/install_keymap.py`)
- `repository.nocturne.custom/` – the Kodi repository add-on; `tools/build_repo.py` + `.github/workflows/publish.yml`
  publish it with the skin to GitHub Pages on every push to `main`
- `deploy.sh` – syncs the skin and keymaps to the box over SSH and reloads them

## Deploy

```sh
./deploy.sh                       # defaults to 192.168.1.142
KODI_HOST=192.168.1.50 ./deploy.sh
```

Requires SSH key login as `root` on the CoreELEC box.

## Install on Kodi (for anyone)

Install through the Kodi repository, not from GitHub's "Code → Download ZIP" or a folder in this repo: the
`addon.xml` files here say `1.0.0`, and only the repository's zips carry the real, current version.

1. Kodi → Settings → System → Add-ons → turn on **Unknown sources**.
2. Settings → File manager → Add source → `https://animate98.github.io/kodi-nocturne-custom/` (name it e.g. `pp`).
3. Add-ons → Install from zip file → `pp` → `repository.nocturne.custom.zip`.
4. Add-ons → Install from repository → Nocturne Custom Repository → Look and feel → Skin →
   **Passe-partout Custom** (or Nocturne Custom). Kodi installs the grid helper and the other dependencies
   with it; POV (`plugin.video.pov`) must already be installed and set up.
5. Settings → Interface → Skin → Passe-partout Custom.

Every push to `main` publishes new versions (`1.0.<run number>`) of all add-ons; Kodi picks them up with its
normal add-on updates (or Add-ons → My add-ons → … → Check for updates).

**Stuck on an old build?** (e.g. a skin installed from a zip by hand): do steps 2–4 above; installing from
the repository replaces it with the current version, and from then on it updates itself.
