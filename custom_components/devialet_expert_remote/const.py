# SPDX-FileCopyrightText: 2026 Renaud Bruyeron <bruyeron@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Constants for the Devialet Expert (non-Pro) Remote integration."""

DOMAIN = "devialet_expert_remote"
CONF_HOST = "host"

UPDATE_INTERVAL = 30  # seconds

# Volume: raw byte → dB = (raw - 195) / 2.0
# VOLUME_LIMIT = -10 dB  ↔  raw 175
# HA 0.0–1.0  ↔  -97.5..-10.0 dB
VOLUME_DB_MIN = -97.5
VOLUME_DB_MAX = -10.0
VOLUME_DB_RANGE = 87.5  # VOLUME_DB_MAX - VOLUME_DB_MIN

MANUFACTURER = "Devialet"
MODEL = "Expert (non-Pro)"
