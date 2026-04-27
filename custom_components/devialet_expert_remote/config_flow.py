# SPDX-FileCopyrightText: 2026 Renaud Bruyeron <bruyeron@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Config flow for the Devialet Expert (non-Pro) Remote integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .backend import DeviMoteBackEnd
from .const import CONF_HOST, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
})


# ConfigFlow drives the "Add Integration" UI shown in Settings → Integrations.
class DevialetConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial configuration UI."""

    VERSION = 1  # Incremented when the stored data schema changes; triggers HA migration hooks.

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            try:
                status = await self.hass.async_add_executor_job(
                    _try_connect, host
                )
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                if not status.get("connected"):
                    errors["base"] = "cannot_connect"
                elif not status.get("crc_ok"):
                    errors["base"] = "invalid_response"
                else:
                    title = (status.get("dev_name") or "Devialet Expert").strip()
                    # Prevents adding the same host twice; aborts if a matching entry already exists.
                    await self.async_set_unique_id(host.lower())
                    self._abort_if_unique_id_configured()
                    # Creates the persistent ConfigEntry and triggers async_setup_entry in __init__.py.
                    return self.async_create_entry(
                        title=title, data={CONF_HOST: host}
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


def _try_connect(host: str) -> dict:
    """Blocking: create a backend with the given host and call update()."""
    backend = DeviMoteBackEnd(host=host)
    return backend.update()
