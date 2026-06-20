#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Renaud Bruyeron <bruyeron@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

if [[ -f "$ENV_FILE" ]]; then
    # shellcheck source=.env
    source "$ENV_FILE"
fi

if [[ -z "${HA_SSH_TARGET:-}" ]]; then
    echo "Error: HA_SSH_TARGET is not set. Add it to .env or export it." >&2
    exit 1
fi

rsync -av --delete --itemize-changes --human-readable \
    "$SCRIPT_DIR/custom_components/devialet_expert_remote/" \
    "${HA_SSH_TARGET}:/config/custom_components/devialet_expert_remote/"

echo "Deployed. Restart Home Assistant to pick up changes."
