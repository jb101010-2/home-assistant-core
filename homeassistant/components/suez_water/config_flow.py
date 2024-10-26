"""Config flow for Suez Water integration."""

from __future__ import annotations

import logging
from typing import Any

from pysuez import SuezClient
from pysuez.client import PySuezError
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_COUNTER_ID, CONF_WITHOUT_OLD, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_COUNTER_ID): str,
    }
)


def validate_input(data: dict[str, Any]) -> None:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    try:
        counter = data.get(CONF_COUNTER_ID)
        client = SuezClient(
            data[CONF_USERNAME],
            data[CONF_PASSWORD],
            counter,
        )
        if not client.check_credentials():
            raise InvalidAuth
        if counter is None:
            data[CONF_COUNTER_ID] = client.counter_finder()
    except PySuezError as ex:
        raise CannotConnect from ex


class SuezWaterConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Suez Water."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_USERNAME])
            self._abort_if_unique_id_configured()
            try:
                await self.hass.async_add_executor_job(validate_input, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                data = {**user_input}
                data[CONF_WITHOUT_OLD] = True
                return self.async_create_entry(
                    title=f"suez_{user_input[CONF_COUNTER_ID]}", data=data
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Reconfigure suez water."""
        if user_input is not None:
            return self.async_update_reload_and_abort(
                self._get_reconfigure_entry(),
                data_updates={CONF_WITHOUT_OLD: user_input.get(CONF_WITHOUT_OLD)},
            )
        entry = self._get_reconfigure_entry()

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_WITHOUT_OLD,
                        default=entry.data.get(CONF_WITHOUT_OLD, False),
                    ): bool
                }
            ),
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
