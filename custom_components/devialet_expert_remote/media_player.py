# SPDX-FileCopyrightText: 2026 Renaud Bruyeron <bruyeron@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""MediaPlayer entity for the Devialet Expert (non-Pro) Remote integration."""

from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_HOST,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    VOLUME_DB_MIN,
    VOLUME_DB_MAX,
    VOLUME_DB_RANGE,
)
from .coordinator import DevialetCoordinator

_SUPPORTED_FEATURES = (
    MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.SELECT_SOURCE
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the media player platform."""
    coordinator: DevialetCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DevialetMediaPlayer(coordinator, entry)])


# CoordinatorEntity subscribes to coordinator updates; properties re-evaluate automatically after each poll.
class DevialetMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Represents a Devialet Expert amplifier."""

    _attr_has_entity_name = True
    _attr_name = None  # None → primary entity: the entity's name equals the device name in the UI.
    # Declares capabilities to HA; controls for unset features are hidden in the UI.
    _attr_supported_features = _SUPPORTED_FEATURES

    def __init__(self, coordinator: DevialetCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = entry.data[CONF_HOST].lower()

    @property
    def device_info(self) -> DeviceInfo:
        # DeviceInfo links this entity to a device in the HA device registry.
        data = self.coordinator.data or {}
        return DeviceInfo(
            # identifiers must be globally unique; used to merge entities from multiple platforms onto one device card.
            identifiers={(DOMAIN, self._entry.data[CONF_HOST].lower())},
            name=(data.get("dev_name") or "Devialet Expert").strip(),
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    @property
    def available(self) -> bool:
        # last_update_success is False if the last _async_update_data raised UpdateFailed.
        return (
            self.coordinator.last_update_success
            and bool((self.coordinator.data or {}).get("connected"))
        )

    @property
    def state(self) -> MediaPlayerState | None:
        if not self.available:
            return None
        power = (self.coordinator.data or {}).get("power", False)
        return MediaPlayerState.ON if power else MediaPlayerState.OFF

    @property
    def volume_level(self) -> float | None:
        raw = (self.coordinator.data or {}).get("volume")
        if raw is None:
            return None
        db = (raw - 195) / 2.0  # device encodes dB as raw byte: dB = (raw − 195) / 2.0
        db = max(VOLUME_DB_MIN, min(VOLUME_DB_MAX, db))
        return (db - VOLUME_DB_MIN) / VOLUME_DB_RANGE  # HA expects volume_level as a 0.0–1.0 float.

    @property
    def is_volume_muted(self) -> bool | None:
        return (self.coordinator.data or {}).get("muted")

    @property
    def source(self) -> str | None:
        data = self.coordinator.data or {}
        ch = data.get("channel")
        ch_list = data.get("ch_list", {})
        if ch is None:
            return None
        return ch_list.get(ch, f"Input {ch}").strip()

    @property
    def source_list(self) -> list[str]:
        ch_list = (self.coordinator.data or {}).get("ch_list", {})
        return [name.strip() for name in ch_list.values()]

    async def async_set_volume_level(self, volume: float) -> None:
        db = volume * VOLUME_DB_RANGE + VOLUME_DB_MIN
        await self.coordinator.async_set_volume(db)
        # Triggers an immediate re-poll so HA reflects the new state without waiting for the next interval.
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        if mute != (self.coordinator.data or {}).get("muted", False):
            await self.coordinator.async_toggle_mute()
            # Triggers an immediate re-poll so HA reflects the new state without waiting for the next interval.
            await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        if not (self.coordinator.data or {}).get("power", False):
            await self.coordinator.async_toggle_power()
            # Triggers an immediate re-poll so HA reflects the new state without waiting for the next interval.
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        if (self.coordinator.data or {}).get("power", False):
            await self.coordinator.async_toggle_power()
            # Triggers an immediate re-poll so HA reflects the new state without waiting for the next interval.
            await self.coordinator.async_request_refresh()

    async def async_select_source(self, source: str) -> None:
        ch_list = (self.coordinator.data or {}).get("ch_list", {})
        for idx, name in ch_list.items():
            if name.strip() == source:
                await self.coordinator.async_set_output(idx)
                # Triggers an immediate re-poll so HA reflects the new state without waiting for the next interval.
                await self.coordinator.async_request_refresh()
                return
