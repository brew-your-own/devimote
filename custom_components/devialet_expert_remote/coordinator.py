# SPDX-FileCopyrightText: 2026 Renaud Bruyeron <bruyeron@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""DataUpdateCoordinator for the Devialet Expert (non-Pro) Remote integration."""

import logging
from datetime import timedelta

# pylint: disable=import-error
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
# pylint: enable=import-error

from .backend import DeviMoteBackEnd
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


# DataUpdateCoordinator polls the device on a fixed schedule and notifies all subscribed entities atomically.
class DevialetCoordinator(DataUpdateCoordinator):
    """Polls the amplifier and serialises all backend access."""

    def __init__(self, hass: HomeAssistant, host: str) -> None:
        self.backend = DeviMoteBackEnd(host=host)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self) -> dict:
        try:
            # async_add_executor_job runs blocking socket I/O on a thread-pool thread, keeping the event loop free.
            return await self.hass.async_add_executor_job(self.backend.update)
        except Exception as exc:
            # UpdateFailed signals a failed poll; HA marks dependent entities unavailable.
            raise UpdateFailed(f"Communication error: {exc}") from exc

    # Command helpers also run via executor so blocking UDP calls don't stall HA.
    async def async_set_volume(self, db_value: float) -> None:
        """Set amplifier volume."""
        await self.hass.async_add_executor_job(self.backend.set_volume, db_value)

    async def async_toggle_power(self) -> None:
        """Toggle amplifier power."""
        await self.hass.async_add_executor_job(self.backend.toggle_power)

    async def async_toggle_mute(self) -> None:
        """Toggle amplifier mute."""
        await self.hass.async_add_executor_job(self.backend.toggle_mute)

    async def async_set_output(self, index: int) -> None:
        """Select amplifier input."""
        await self.hass.async_add_executor_job(self.backend.set_output, index)
