"""Config flow for Suez Water integration."""

from __future__ import annotations

import logging
from typing import Any

from pysuez import PySuezError, SuezClient, ContractResult
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
    }
)
STEP_USER_CONTRACT_SCHEMA = vol.Schema(
    {
        vol.Required("contract"): ContractResult,
    }
)

STEP_USER_CONFIRMATION_SCHEMA = vol.Schema(
    {
        **STEP_USER_DATA_SCHEMA.schema,
        **STEP_USER_CONTRACT_SCHEMA.schema,
        vol.Required(CONF_COUNTER_ID): str
    }
)


async def connect_and_get_contracts(data: dict[str, Any]) -> None:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    try:
        client = SuezClient(
            data[CONF_USERNAME],
            data[CONF_PASSWORD],
        )
        try:
            if not await client.check_credentials():
                raise InvalidAuth
            contracts = await client.get_all_contracts()
            if len(contracts) == 1:
                todo check if there is a counter
            if len(contracts) > 1:
                raise MultipleContracts(contracts=contracts)
            raise NoContractFound
        except PySuezError as ex:
            raise CannotConnect from ex

        if counter_id is None:
            try:
                data[CONF_COUNTER_ID] = await client.find_counter()
            except PySuezError as ex:
                raise CounterNotFound from ex
    finally:
        await client.close_session()


class SuezWaterConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Suez Water."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial setup step."""
        async def login_form(user_input: dict[str, Any])-> SuezClient:
            client = SuezClient(
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )

            if not await client.check_credentials():
                raise InvalidAuth
            return client
        
        async def contract_form(client: SuezClient)-> ConfigFlowResult:
            # Show contract along their given counter and error message 7
            # if no counter is defined for given contract
            contracts = await client.get_all_contracts(with_counter=True)
            return self.async_show_form(
                step_id="init",
                data_schema=self.add_suggested_values_to_schema(
                    STEP_USER_CONTRACT_SCHEMA, {
                        "contract": contracts
                    }
                ),
            )
        
    
        async def confirmation_form()-> ConfigFlowResult:
            pass

        try:
            res = login_form()
            if res = FORM:
                res = contract_form()
            if res = FORM
                res = confirmation_form()
            if res = CREATE_ENTRY
                unique_id = contract.fullRefFormat
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except CounterNotFound:
            errors["base"] = "counter_not_found"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"

            1 config entry per contract ?
            1 device per contract
            device can become stale if changed and replace by another 

        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                await connect_and_get_contracts(user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CounterNotFound:
                errors["base"] = "counter_not_found"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                counter_id = str(user_input[CONF_COUNTER_ID])
                await self.async_set_unique_id(counter_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=counter_id, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={"tout_sur_mon_eau": "Tout sur mon Eau"},
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class CounterNotFound(HomeAssistantError):
    """Error to indicate we failed to automatically find the counter id."""

class NoContractFound(HomeAssistantError):
    """Error to indicate that no contract was found for the given user."""


class MultipleContracts(HomeAssistantError):
    """Error to indicate that the user has multiple contract and should select one."""
    contracts: list[ContractResult]


    def __init__(
        self,
        *args: object,
        translation_domain: str | None = None,
        translation_key: str | None = None,
        translation_placeholders: dict[str, str] | None = None,
        contracts: list[ContractResult]
    ) -> None:
        """Initialize exception."""
        super().__init__(*args, translation_domain=translation_domain,translation_key=translation_key,
                         translation_placeholders=translation_placeholders)
        self.contracts = contracts

