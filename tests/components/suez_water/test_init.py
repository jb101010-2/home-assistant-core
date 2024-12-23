"""Test Suez_water integration initialization."""

from unittest.mock import AsyncMock

from freezegun.api import FrozenDateTimeFactory

from homeassistant.components.suez_water.config_flow import SuezWaterConfigFlow
from homeassistant.components.suez_water.const import (
    CONF_COUNTER_ID,
    DATA_REFRESH_INTERVAL,
    DOMAIN,
)
from homeassistant.components.suez_water.coordinator import (
    PySuezConnexionError,
    PySuezError,
)
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant

from . import setup_integration
from .conftest import MOCK_DATA

from tests.common import MockConfigEntry, async_fire_time_changed


async def test_initialization_invalid_credentials(
    hass: HomeAssistant,
    suez_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that suez_water can't be loaded with invalid credentials."""

    suez_client.check_credentials.return_value = False
    await setup_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR


async def test_initialization_setup_api_error(
    hass: HomeAssistant,
    suez_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that suez_water needs to retry loading if something failed."""

    suez_client.check_credentials.side_effect = PySuezError("Test failure")
    await setup_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_initialization_setup_auth_needed(
    hass: HomeAssistant,
    suez_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that suez_water needs to retry loading if api failed to connect during setup."""

    suez_client.check_credentials.side_effect = PySuezConnexionError(
        "Authentication failure"
    )
    await setup_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_initialization_refresh_auth_needed(
    hass: HomeAssistant,
    suez_client: AsyncMock,
    freezer: FrozenDateTimeFactory,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that suez_water needs reauth flow is started if login fail during refresh."""
    await setup_integration(hass, mock_config_entry)
    assert mock_config_entry.state is ConfigEntryState.LOADED

    suez_client.check_credentials.side_effect = PySuezConnexionError(
        "Authentication failure"
    )

    freezer.tick(DATA_REFRESH_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(True)

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert mock_config_entry.async_get_active_flows(hass, {SOURCE_REAUTH})


async def test_migration_version_rollback(
    hass: HomeAssistant,
    suez_client: AsyncMock,
) -> None:
    """Test that a version rollback does not impact config."""
    future_entry = MockConfigEntry(
        unique_id=MOCK_DATA[CONF_COUNTER_ID],
        domain=DOMAIN,
        title="Suez mock device",
        data=MOCK_DATA,
        version=SuezWaterConfigFlow.VERSION + 1,
    )
    await setup_integration(hass, future_entry)
    assert future_entry.state is ConfigEntryState.MIGRATION_ERROR


async def test_no_migration_current_version(
    hass: HomeAssistant,
    suez_client: AsyncMock,
) -> None:
    """Test that a current version does not migrate."""
    future_entry = MockConfigEntry(
        unique_id=MOCK_DATA[CONF_COUNTER_ID],
        domain=DOMAIN,
        title="Suez mock device",
        data=MOCK_DATA,
        version=SuezWaterConfigFlow.VERSION,
    )
    await setup_integration(hass, future_entry)
    assert future_entry.state is ConfigEntryState.LOADED
    assert future_entry.unique_id == MOCK_DATA[CONF_COUNTER_ID]


async def test_migration_version_1_to_2(
    hass: HomeAssistant,
    suez_client: AsyncMock,
) -> None:
    """Test that a migration from 1 to 2 change unique_id."""

    broken_data = MOCK_DATA.copy()
    broken_data.pop(CONF_COUNTER_ID)

    past_entry = MockConfigEntry(
        unique_id=MOCK_DATA[CONF_USERNAME],
        domain=DOMAIN,
        title=MOCK_DATA[CONF_USERNAME],
        data=broken_data,
        version=1,
        minor_version=0,
    )
    await setup_integration(hass, past_entry)
    assert past_entry.state is ConfigEntryState.MIGRATION_ERROR

    past_entry = MockConfigEntry(
        unique_id=MOCK_DATA[CONF_USERNAME],
        domain=DOMAIN,
        title=MOCK_DATA[CONF_USERNAME],
        data=MOCK_DATA,
        version=1,
        minor_version=0,
    )

    await setup_integration(hass, past_entry)
    assert past_entry.state is ConfigEntryState.LOADED
    assert past_entry.unique_id == str(MOCK_DATA[CONF_COUNTER_ID])
    assert past_entry.title == MOCK_DATA[CONF_USERNAME]
