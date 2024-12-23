"""Config flow for Suez Water integration."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from pysuez import PySuezError, SuezClient
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_COUNTER_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_COUNTER_ID): str,
    }
)
STEP_REAUTH_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(data: dict[str, Any]) -> str | None:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    async def validate() -> None:
        try:
            counter_id = data.get(CONF_COUNTER_ID)
            client = SuezClient(
                data[CONF_USERNAME],
                data[CONF_PASSWORD],
                counter_id,
            )
            try:
                if not await client.check_credentials():
                    raise InvalidAuth
            except PySuezError as ex:
                raise CannotConnect from ex

            if counter_id is None:
                try:
                    data[CONF_COUNTER_ID] = await client.find_counter()
                except PySuezError as ex:
                    raise CounterNotFound from ex
        finally:
            await client.close_session()

    try:
        await validate()
    except CannotConnect:
        return "cannot_connect"
    except InvalidAuth:
        return "invalid_auth"
    except CounterNotFound:
        return "counter_not_found"
    except Exception:
        _LOGGER.exception("Unexpected exception")
        return "unknown"
    else:
        return None


class SuezWaterConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Suez Water."""

    VERSION = 2
    MINOR_VERSION = 0

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            result = await validate_input(user_input)
            if not result:
                await self.async_set_unique_id(user_input[CONF_COUNTER_ID])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_COUNTER_ID], data=user_input
                )
            errors["base"] = result

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={"tout_sur_mon_eau": "Tout sur mon Eau"},
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Perform reauth upon an API authentication error."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that reauth is required."""
        errors: dict[str, str] = {}

        if user_input is not None:
            result = await validate_input(user_input)
            if not result:
                await self.async_set_unique_id(user_input[CONF_COUNTER_ID])
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data=user_input,
                )
            errors["base"] = result

        updated = self._get_reauth_entry()
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_REAUTH_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "tout_sur_mon_eau": "Tout sur mon Eau",
                "meter_id": updated.data[CONF_COUNTER_ID],
            },
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class CounterNotFound(HomeAssistantError):
    """Error to indicate we failed to automatically found the counter id."""
