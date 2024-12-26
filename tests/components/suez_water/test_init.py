"""Test Suez_water integration initialization."""

from unittest.mock import AsyncMock

from homeassistant.components.suez_water.coordinator import PySuezError
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration

from tests.common import MockConfigEntry


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
    """Test that suez_water needs to retry loading if api failed to connect."""

    suez_client.check_credentials.side_effect = PySuezError("Test failure")
    await setup_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_successefuly(
    hass: HomeAssistant,
    suez_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that shutdown has been requested to pysuez on unload."""
    await setup_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert suez_client.close_session.call_count == 0
    assert hass.config_entries.async_get_entry(mock_config_entry.entry_id) is not None

    suez_client.close_session.side_effect = Exception("Fail to close session")
    assert not await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert suez_client.close_session.call_count == 1
    assert (
        hass.config_entries.async_get_entry(mock_config_entry.entry_id).state
        is ConfigEntryState.LOADED
    )

    suez_client.close_session.side_effect = None
    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert suez_client.close_session.call_count == 2
    assert (
        hass.config_entries.async_get_entry(mock_config_entry.entry_id).state
        is ConfigEntryState.NOT_LOADED
    )
