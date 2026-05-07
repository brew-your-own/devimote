<!--
SPDX-FileCopyrightText: 2026 Renaud Bruyeron <bruyeron@gmail.com>

SPDX-License-Identifier: CC0-1.0
-->

# DeviMote — project notes for Claude

## What this project is

An unofficial remote control for the Devialet Expert (non-Pro, i.e. before the Core Infinity board) amplifier, written in
Python. The amplifier communicates over UDP on the local network; no official API exists —
the protocol was reverse-engineered via Wireshark.

Three interfaces are provided:

- **CLI** (`devialet`): status display and control via subcommands, no GUI dependency.
- **Kivy GUI** (`devialet-gui`): original graphical interface.
- **Home Assistant custom component** (`custom_components/devialet_expert_remote`): MediaPlayer entity with volume, mute, power, and source selection. Minimum HA 2024.4.0.

---

## Repository layout

```
src/
  backend.py    Pure-Python communication layer. No Kivy dependency.
  cli.py        Click-based CLI entry point.
  devimote.py   Kivy GUI app. Imports DeviMoteBackEnd from backend.py.
  devimote.kv   Kivy declarative layout.
custom_components/devialet_expert_remote/
  __init__.py   Integration setup/teardown (async_setup_entry, async_unload_entry).
  coordinator.py  DataUpdateCoordinator: polls amp every 30 s, notifies entities.
  config_flow.py  ConfigFlow: "Add Integration" UI in HA Settings.
  media_player.py MediaPlayerEntity: volume, mute, power, source selection.
  backend.py    Canonical backend. src/backend.py is a symlink to this file.
  const.py      Domain, update interval, volume range constants.
  manifest.json HA integration metadata.
  strings.json  UI strings (English).
wireshark/
  dec.lua       Wireshark dissector for DEC protocol.
  des.lua       Wireshark dissector for DES protocol.
pyproject.toml  Project metadata, dependencies, entry points.
.python-version Pins the project to Python 3.12 (kivy requires it).
.env.example    Documents supported environment variables.
deploy-ha-dev.sh  Deploys custom_components/ to HA via rsync over SSH.
hacs.json       HACS distribution metadata.
```

---

## Architecture

### Communication protocol (backend.py)

The amplifier broadcasts UDP status packets on port 45454 at ~10 Hz.
`DeviMoteBackEnd.update()` binds to that port, receives one packet (2 s timeout),
and parses it into `self.status`.

Commands are sent as 142-byte UDP packets to port 45455, repeated 4 times for
reliability. Each packet is framed with a `0x44 0x72` header and a
CRC-16/CCITT-FALSE checksum over the first 12 bytes.

Key status fields decoded from the 512-byte status packet:

| Field | Byte(s) | Notes |
|-------|---------|-------|
| `dev_name` | 19–50 | UTF-8, 32 bytes |
| `ch_list` | 52–301 | 15 × 17-byte entries: 1-byte enabled flag + 16-byte name |
| `power` | 307 bit 7 | `0x80` mask |
| `muted` | 308 bit 1 | `0x02` mask |
| `channel` | 308 bits 2–5 | `0x3c` mask, right-shifted 2 |
| `volume` | 310 | Raw byte; dB = `(raw - 195) / 2.0` |

The CRC is `binascii.crc_hqx(data, 0xFFFF)` — standard library, verified equivalent
to the original hand-rolled implementation via test vectors including the canonical
CCITT-FALSE check value `0x29B1` for `123456789`.

### Volume encoding

`set_volume(db_value)` takes a float in dB. The backend silently clamps values above
`VOLUME_LIMIT = -10 dB`. The CLI enforces this limit with an explicit error before
connecting, so the user gets a clear message rather than silent clamping.

Volume display conversion (from the raw status byte): `db = (raw - 195) / 2.0`

### Source selection

`status['ch_list']` is a `dict[int, str]` mapping channel index → name. The CLI
matches by case-insensitive substring and errors on 0 or >1 matches.
`set_output(index)` sends the command.

`ch_list` is rebuilt from scratch on every `update()` call (not accumulated) so it
always reflects the amp's current configuration.

---

## Home Assistant integration

### Architecture

| File | HA concept | Role |
|------|-----------|------|
| `__init__.py` | `ConfigEntry` / `async_setup_entry` | Creates coordinator, forwards to platforms |
| `coordinator.py` | `DataUpdateCoordinator` | Polls amp every 30 s via executor; command helpers also run via executor |
| `config_flow.py` | `ConfigFlow` | Validates host at setup time; prevents duplicate entries via unique ID |
| `media_player.py` | `CoordinatorEntity` + `MediaPlayerEntity` | Exposes state and controls; reads live data from coordinator |

### Volume handling

HA sends `volume_level` as a 0.0–1.0 float. The entity converts to dB
(`db = volume * 87.5 - 97.5`), then `set_volume()` rounds to the nearest 0.5 dB
before encoding — the hardware only supports 0.5 dB steps and `_db_convert`
crashes on non-multiples.

### backend.py

`custom_components/devialet_expert_remote/backend.py` is the canonical copy.
`src/backend.py` is a symlink to it. Edit only the custom_components version.

---

## Dependency groups (uv)

| Group | Install | Purpose |
|-------|---------|---------|
| *(default)* | `uv sync` | CLI runtime: `click`, `python-dotenv` |
| `dev` | `uv sync --group dev` | `pylint` for linting |
| `gui` | `uv sync --group gui` | `kivy[base]` for the Kivy GUI |

Run linting: `uv run pylint $(git ls-files '*.py' | grep -v 'src/backend\.py')`

`src/backend.py` is excluded because it is a symlink to the canonical
`custom_components/devialet_expert_remote/backend.py`; passing both would cause a
false R0801 duplicate-code warning.

---

## Configuration (.env)

```
DEVIALET_IP=mydevialet-amp.home.arpa   # hostname or IP; optional, auto-discovered if unset
HA_SSH_TARGET=user@homeassistant.local # SSH target used by deploy-ha-dev.sh
```

`DEVIALET_IP` accepts a hostname or an IP.
If set and the discovered device IP doesn't match, a warning is printed to stderr
but the connection proceeds (auto-discovered IP wins).

`HA_SSH_TARGET` is only used by `deploy-ha-dev.sh` to rsync the custom component
to the HA host.

---

## Workflow

- **Do not commit unless explicitly asked.** Make changes, then wait for the user to say "commit".

## Style and conventions

- **No comments** unless the why is non-obvious (e.g. the 4× retry in `_send_command`,
  the magic byte offsets in `update()`).
- Pylint score must stay at **10.00/10** across all tracked `.py` files (excluding the
  `src/backend.py` symlink). HA component files use `# pylint: disable/enable=import-error`
  blocks around HA imports (unavailable outside HA). `devimote.py` does the same for
  Kivy imports. `max-line-length = 120` is set in `pyproject.toml` (HA convention).
- SPDX licence headers on all source files (GPL-3.0-or-later for Python, CC0-1.0 for
  config/CI files). REUSE compliance is checked by CI.
- Python 3.12 is pinned via `.python-version`. Kivy 2.3.1 does not ship a compiled
  SDL2 window backend for Python 3.13/3.14.
- The backend (`backend.py`) must remain free of Kivy imports so the CLI works
  without the gui dependency group.
- `devimote.py` should not be modified unless the GUI behaviour needs to change;
  prefer adding features to `cli.py` or `backend.py`.
