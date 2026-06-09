<!--
SPDX-FileCopyrightText: 2020 Dimitris Lampridis <dlampridis@gmail.com>

SPDX-License-Identifier: CC0-1.0
-->

# DeviMote

Unofficial remote control for Devialet Expert (non-Pro) amplifiers written in Python.

![Lint and Test](https://github.com/gnulabis/devimote/workflows/Lint%20and%20Test/badge.svg?branch=main)
![REUSE](https://github.com/gnulabis/devimote/workflows/REUSE/badge.svg?branch=main)

The amplifier is controlled over UDP on the local network. There is no official API —
the protocol was reverse-engineered with Wireshark. "Non-Pro" means hardware from before
the Core Infinity board.

This repository provides two things:

- **`pydevialet_expert_nonpro`** — a small, dependency-free Python library implementing the
  UDP protocol. This is the publishable artifact, installable from PyPI and reusable by any
  application (CLIs, GUIs, Home Assistant, …).
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
pip install -e ".[dev,gui]"
pytest                                         # unit tests (no amplifier needed)
pylint src/pydevialet_expert_nonpro tests gui  # must stay at 10.00/10
reuse lint                                     # licensing compliance
```
