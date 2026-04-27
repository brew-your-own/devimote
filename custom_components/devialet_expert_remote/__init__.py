# SPDX-FileCopyrightText: 2026 Renaud Bruyeron <bruyeron@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Devialet Expert (non-Pro) Remote integration for Home Assistant."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_HOST, DOMAIN
from .coordinator import DevialetCoordinator

PLATFORMS = ["media_player"]


# Called by HA once per ConfigEntry (one per configured device) when HA starts or the entry is enabled.
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    coordinator = DevialetCoordinator(hass, entry.data[CONF_HOST])
    # Forces one successful poll before entities are created; raises ConfigEntryNotReady on failure.
    await coordinator.async_config_entry_first_refresh()

    # hass.data[DOMAIN] is the standard per-domain runtime store keyed by entry_id.
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Delegates to async_setup_entry() in each platform file (e.g. media_player.py).
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


# Called when the entry is removed or disabled; must clean up all resources.
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
