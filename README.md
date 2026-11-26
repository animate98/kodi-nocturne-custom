# Nocturne Custom

A personal Kodi skin for CoreELEC (Kodi 22), forked from
[Nocturne](https://github.com/KarmaMole/kodi-skins) v0.9.19 by KarmaMole.
Licensed under GPL-2.0-or-later, same as the original (see `skin.nocturne.custom/LICENSE.txt`).

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

## Install on Kodi from GitHub

1. Kodi → Settings → File manager → Add source → `https://animate98.github.io/kodi-nocturne-custom/`
2. Add-ons → Install from zip file → that source → `repository.nocturne.custom-1.0.0.zip`
3. Add-ons → Install from repository → Nocturne Custom Repository → Look and feel → Skin → Nocturne Custom

Every push to `main` publishes a new version (`1.0.<run number>`); Kodi picks it up with its normal add-on updates.
