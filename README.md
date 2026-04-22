<!--
SPDX-FileCopyrightText: 2020 Dimitris Lampridis <dlampridis@gmail.com>

SPDX-License-Identifier: CC0-1.0
-->

# DeviMote
Unofficial remote control for Devialet Expert amplifiers written in Python

![Pylint](https://github.com/gnulabis/devimote/workflows/Pylint/badge.svg?branch=main)
![REUSE](https://github.com/gnulabis/devimote/workflows/REUSE/badge.svg?branch=main)

![](doc/images/devimote_demo.gif)

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```bash
cp .env.example .env   # set DEVIALET_IP if needed (hostname or IP; auto-discovered if unset)
uv sync                # installs CLI dependencies
```

## CLI

```bash
uv run devialet status              # show device status
uv run devialet volume -- -15.0    # set volume in dB (use -- before negative values)
uv run devialet mute                # toggle mute
uv run devialet power               # toggle power (on/standby)
uv run devialet source Toslink      # select source by name (case-insensitive partial match)
```

Example output of `devialet status`:

```
Device:  My Devialet
IP:      192.168.1.100
Power:   ON
Volume:  -12.0 dB
Muted:   No
Source:  Toslink (2)
Sources: Toslink (2), Phono (4), AES (5)
```

Volume is capped at -10 dB. The CLI will error if you try to exceed it.

## GUI

```bash
uv sync --group gui    # installs Kivy
uv run devialet-gui
```
