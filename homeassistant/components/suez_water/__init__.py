"""The Suez Water integration."""

from __future__ import annotations

import logging

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import SuezWaterConfigEntry, SuezWaterCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: SuezWaterConfigEntry) -> bool:
    """Set up Suez Water from a config entry."""

    coordinator = SuezWaterCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: SuezWaterConfigEntry) -> bool:
    """Unload suez_water config entry."""

    try:
        await entry.runtime_data.close_session()
    except Exception:
        _LOGGER.exception("Failed to close session to suez API")
        return False
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
