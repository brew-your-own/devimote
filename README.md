<!--
SPDX-FileCopyrightText: 2020 Dimitris Lampridis <dlampridis@gmail.com>

SPDX-License-Identifier: CC0-1.0
-->

# DeviMote

Unofficial remote control for Devialet Expert (non-Pro) amplifiers written in Python.

![Lint and Test](https://github.com/gnulabis/devimote/workflows/Lint%20and%20Test/badge.svg)
![REUSE](https://github.com/gnulabis/devimote/workflows/REUSE/badge.svg)

The amplifier is controlled over UDP on the local network. There is no official API —
the protocol was reverse-engineered with Wireshark. "Non-Pro" means hardware from before
the Core Infinity board.

This repository provides four things:

- **`pydevialet_expert_nonpro`** — a small, dependency-free Python library implementing the
  UDP protocol. This is the publishable artifact, installable from PyPI and reusable by any
  application (CLIs, GUIs, Home Assistant, …).
- **A CLI** (`devialet`) — a command-line remote, installed as an optional extra.
- **A Home Assistant custom component** (`custom_components/devialet_expert_remote`) — a
  `media_player` entity installable via HACS.
- **A Kivy GUI** (`gui/devimote.py`) — the original graphical remote, now a thin consumer of
  the library. It is a standalone script and is *not* part of the published package.

## Library

```bash
pip install pydevialet-expert-nonpro
```

```python
from pydevialet_expert_nonpro import DeviMoteBackEnd

amp = DeviMoteBackEnd()             # or DeviMoteBackEnd(host="mydevialet.local")
status = amp.update()              # receive and decode one status broadcast
print(status["dev_name"], status["volume"])

amp.set_volume(-20.0)              # volume in dB (clamped at -10 dB)
amp.toggle_mute()
amp.toggle_power()
amp.set_output(2)                  # select input by channel index
```

`update()` returns the status dictionary (`dev_name`, `ip`, `ch_list`, `power`, `muted`,
`channel`, `volume`, `connected`, `crc_ok`). `DevialetExpertNonPro` is available as an alias
of `DeviMoteBackEnd`.

All calls are blocking; run them on a worker thread if you need async behaviour.

## CLI

Install the `cli` extra to get the `devialet` command:

```bash
pip install "pydevialet-expert-nonpro[cli]"
```

Or run without installing via `uv`:

```bash
uvx --from "pydevialet-expert-nonpro[cli]" devialet --help
```

```
Usage: devialet [OPTIONS] COMMAND [ARGS]...

Commands:
  status  Show current amplifier status
  volume  Set volume in dB
  mute    Toggle mute on/off
  power   Toggle power (on/standby)
  source  Select input source by name (case-insensitive partial match)
```

The CLI auto-discovers the amplifier by listening for its UDP broadcast. You can optionally
pin it to a specific device by setting `DEVIALET_IP` in a `.env` file (copy `.env.example`):

```bash
cp .env.example .env   # then edit DEVIALET_IP=<your-amp-ip>
```

```bash
devialet status
devialet volume -- -20.5   # use -- before negative values
devialet mute
devialet power
devialet source analog
```

## Home Assistant

The custom component exposes the amplifier as a `media_player` entity with volume, mute,
power, and source selection. It is installable via [HACS](https://www.hacs.xyz) or manually.

**Via HACS** — add this repository as a custom repository, then install
"Devialet Expert (non-Pro) Remote".

**Manually** — copy `custom_components/devialet_expert_remote/` into your HA
`config/custom_components/` directory and restart Home Assistant.

Then go to Settings → Integrations → Add Integration → search for "Devialet".

The component polls the amplifier every 30 seconds and also refreshes immediately after any
command (volume, mute, power, source).

For development, deploy directly to a local HA instance over SSH:

```bash
cp .env.example .env   # set HA_SSH_TARGET=homeassistant@<your-ha-host>
./deploy-ha-dev.sh
```

## GUI

The Kivy GUI is a standalone script. Install the project with the `gui` extra and run it:

```bash
pip install -e ".[gui]"
python gui/devimote.py
```

![](doc/images/devimote_demo.gif)

> [!NOTE]  
> the Kivy 2.3.1 dependency [does not install with Python 3.14](https://github.com/kivy/kivy/issues/9225). If you want to test/use the GUI, you must use Python 3.13 or earlier.

## Development

```bash
pip install -e ".[dev,cli,gui]"
pytest                                         # unit tests (no amplifier needed)
pylint src/pydevialet_expert_nonpro tests gui  # must stay at 10.00/10
reuse lint                                     # licensing compliance
```
