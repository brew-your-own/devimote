# DeviMote — project notes for Claude

## What this project is

An unofficial remote control for the Devialet Expert (non-Pro, i.e. before the Core Infinity board) amplifier, written in
Python. The amplifier communicates over UDP on the local network; no official API exists —
the protocol was reverse-engineered via Wireshark.

Two interfaces are provided:

- **CLI** (`devialet`): status display and control via subcommands, no GUI dependency.
- **Kivy GUI** (`devialet-gui`): original graphical interface.

---

## Repository layout

```
src/
  backend.py    Pure-Python communication layer. No Kivy dependency.
  cli.py        Click-based CLI entry point.
  devimote.py   Kivy GUI app. Imports DeviMoteBackEnd from backend.py.
  devimote.kv   Kivy declarative layout.
wireshark/
  dec.lua       Wireshark dissector for DEC protocol.
  des.lua       Wireshark dissector for DES protocol.
pyproject.toml  Project metadata, dependencies, entry points.
.python-version Pins the project to Python 3.12 (kivy requires it).
.env.example    Documents supported environment variables.
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

---

## Dependency groups (uv)

| Group | Install | Purpose |
|-------|---------|---------|
| *(default)* | `uv sync` | CLI runtime: `click`, `python-dotenv` |
| `dev` | `uv sync --group dev` | `pylint` for linting |
| `gui` | `uv sync --group gui` | `kivy[base]` for the Kivy GUI |

Run linting: `uv run pylint src/backend.py src/cli.py`

---

## Configuration (.env)

```
DEVIALET_IP=mydevialet-amp.home.arpa   # hostname or IP; optional, auto-discovered if unset
```

`DEVIALET_IP` accepts a hostname or an IP.
If set and the discovered device IP doesn't match, a warning is printed to stderr
but the connection proceeds (auto-discovered IP wins).

---

## Workflow

- **Do not commit unless explicitly asked.** Make changes, then wait for the user to say "commit".

## Style and conventions

- **No comments** unless the why is non-obvious (e.g. the 4× retry in `_send_command`,
  the magic byte offsets in `update()`).
- Pylint score must stay at **10.00/10** across `backend.py` and `cli.py`.
  `devimote.py` has a `# pylint: disable=import-error` on the backend import
  because Kivy is not installed in the default (non-gui) venv.
- SPDX licence headers on all source files (GPL-3.0-or-later for Python, CC0-1.0 for
  config/CI files). REUSE compliance is checked by CI.
- Python 3.12 is pinned via `.python-version`. Kivy 2.3.1 does not ship a compiled
  SDL2 window backend for Python 3.13/3.14.
- The backend (`backend.py`) must remain free of Kivy imports so the CLI works
  without the gui dependency group.
- `devimote.py` should not be modified unless the GUI behaviour needs to change;
  prefer adding features to `cli.py` or `backend.py`.
