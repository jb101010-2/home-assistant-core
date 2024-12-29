"""The Suez Water integration."""

from __future__ import annotations

import logging

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_COUNTER_ID
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
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(
    hass: HomeAssistant, config_entry: SuezWaterConfigEntry
) -> bool:
    """Migrate old suez water config entry."""
    _LOGGER.debug(
        "Migrating configuration from version %s.%s",
        config_entry.version,
        config_entry.minor_version,
    )

    if config_entry.version > 2:
        return False

    if config_entry.version == 1:
        # Migrate to version 2
        counter_id = config_entry.data.get(CONF_COUNTER_ID)
        unique_id = str(counter_id)

        hass.config_entries.async_update_entry(
            config_entry,
            unique_id=unique_id,
            version=2,
        )

    _LOGGER.debug(
        "Migration to configuration version %s.%s successful",
        config_entry.version,
        config_entry.minor_version,
    )

    return True


# Devices TODO list
# 1. Find a way to uniquely identify integration ?
# 2. Dynamically create device based on meter id or client ref ?
# 3. One coordinator for all devices vs one per device ?
# 4. How to register device ?
# 5. How to remember that user removed device ? device disabled ?
# 6. Configuration_url => path to reconfigure flow ?
# 7. Fetch data in coordinator per device ?
# 8. ??????????

#  Suez action when changing contract
# /mon-compte-en-ligne/redirect/98-5537172589?redirect=/mon-compte-en-ligne/tableau-de-bord
#         t.REDIRECT_CEL_URL = "/mon-compte-en-ligne/redirect/:fullRefFormat?redirect=:pathname",
# var r = t.fullRefFormat, n = window.location.pathname;
# window.location.pathname => '/mon-compte-en-ligne/tableau-de-bord'
#                             window.location.href = p.REDIRECT_CEL_URL.replace(":fullRefFormat", r).replace(":pathname", n)
