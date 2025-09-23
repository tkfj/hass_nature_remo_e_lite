from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .api import NatureRemoEApi, NatureRemoEApiError
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_DEVICE_ID,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ACCESS_TOKEN): str,
        vol.Required(CONF_DEVICE_ID, default="nature_remo_e_power"): str,
    }
)

STEP_OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(
            int, vol.Range(min=5, max=3600)
        )
    }
)

async def _validate_and_get_unique_id(hass: HomeAssistant, access_token: str, device_id: str) -> str:
    api = NatureRemoEApi(hass, access_token)
    await api.async_validate()
    return f"{device_id}"

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            token = user_input[CONF_ACCESS_TOKEN]
            device_id = user_input[CONF_DEVICE_ID]
            try:
                unique_id = await _validate_and_get_unique_id(self.hass, token, device_id)
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Nature Remo E ({device_id})",
                    data={
                        CONF_ACCESS_TOKEN: token,
                        CONF_DEVICE_ID: device_id,
                    },
                )
            except NatureRemoEApiError:
                errors["base"] = "auth"

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors)

    async def async_step_import(self, user_input: dict | None = None) -> FlowResult:
        # YAML import未対応（UI前提）
        return self.async_abort(reason="not_supported")

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=STEP_OPTIONS_SCHEMA,
        )
