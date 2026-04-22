..
   SPDX-FileCopyrightText: 2020 Dimitris Lampridis <dlampridis@gmail.com>
   SPDX-License-Identifier: CC0-1.0

=========
Changelog
=========

Unreleased
==========

Architecture
------------
- Extracted communication backend into ``src/backend.py``, decoupling it from the
  Kivy GUI. The backend has no GUI dependency and can be imported standalone.
- Replaced hand-rolled CRC-16/CCITT-FALSE with ``binascii.crc_hqx`` from the
  standard library (verified equivalent via test vectors).
- Added ``pyproject.toml`` with ``uv`` as the project manager. Dependencies are
  split into groups: default (CLI), ``dev`` (pylint), ``gui`` (kivy).
- Pinned project to Python 3.12 (Kivy 2.3.1 does not ship a compiled SDL2 backend
  for Python 3.13+).

Added
-----
- CLI interface (``uv run devialet``): ``status``, ``volume``, ``mute``, ``power``,
  and ``source`` subcommands, powered by Click.
- ``.env`` support via ``python-dotenv``: ``DEVIALET_IP`` accepts a hostname or IP
  to identify the target amplifier; auto-discovered from UDP broadcast if unset.
- Volume safety: the CLI rejects volume values above ``-10 dB`` with an explicit
  error instead of silently clamping.
- GUI entry point (``uv run devialet-gui``) installable via ``uv sync --group gui``.

upstream (e5963bd)
==================

Added
-----
- Kivy GUI remote control for Devialet Expert amplifiers (non-Pro hardware).
- UDP protocol implementation: receives 512-byte status broadcasts on port 45454,
  sends 142-byte control packets to port 45455.
- Controls: power toggle, mute toggle, volume (dB), source/output selection.
- Status display: device name, power state, mute state, volume, active source.
- Shared UDP socket option (``SO_REUSEADDR``) to allow concurrent listeners.
- Wireshark dissectors for the DEC and DES protocols (Lua).
- Pylint and REUSE compliance CI.
