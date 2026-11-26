# Nocturne Custom

A personal Kodi skin for CoreELEC (Kodi 22), forked from
[Nocturne](https://github.com/KarmaMole/kodi-skins) v0.9.19 by KarmaMole.
Licensed under GPL-2.0-or-later, same as the original (see `skin.nocturne.custom/LICENSE.txt`).

## Layout

- `skin.nocturne.custom/` – the skin add-on itself (installed to `/storage/.kodi/addons/` on the box)
  - `colors/defaults.xml` – color palette
  - `1080i/` – window and include XML
  - `media/` – textures
- `deploy.sh` – syncs the skin to the box over SSH and reloads it

## Deploy

```sh
./deploy.sh                       # defaults to 192.168.1.142
KODI_HOST=192.168.1.50 ./deploy.sh
```

Requires SSH key login as `root` on the CoreELEC box.
