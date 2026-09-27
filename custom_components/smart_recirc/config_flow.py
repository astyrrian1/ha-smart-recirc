"""Manual/discovered setup with explicit connection side-effect notice."""

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .api import Client, RecircError, UnsupportedAuthentication
from .const import (
    CONF_ACKNOWLEDGE,
    CONF_FLOW_METER,
    DOMAIN,
    FLOW_METER_1,
    FLOW_METER_3_4,
    FLOW_METER_UNKNOWN,
)


class SmartRecircConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._host = ""
        self._port = 5438

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SmartRecircOptionsFlow()

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> ConfigFlowResult:
        self._host = discovery_info.host
        self._port = discovery_info.port or 5438
        self._async_abort_entries_match({CONF_HOST: self._host})
        # No device connection until the user acknowledges connection behavior.
        return await self.async_step_user()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors = {}
        if user_input is not None:
            if not user_input.get(CONF_ACKNOWLEDGE):
                errors[CONF_ACKNOWLEDGE] = "acknowledgment_required"
            else:
                client = Client(user_input[CONF_HOST], user_input[CONF_PORT])
                try:
                    info = await client.identify()
                    await client.read_state()
                except UnsupportedAuthentication:
                    errors["base"] = "unsupported_authentication"
                except RecircError:
                    errors["base"] = "cannot_connect"
                else:
                    await self.async_set_unique_id(info.identity)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=info.name,
                        data={CONF_HOST: user_input[CONF_HOST], CONF_PORT: user_input[CONF_PORT]},
                    )
                finally:
                    await client.close()
        return self.async_show_form(
            step_id="user",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=self._host): str,
                    vol.Required(CONF_PORT, default=self._port): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=65535)
                    ),
                    vol.Required(CONF_ACKNOWLEDGE, default=False): bool,
                }
            ),
        )

    async def async_step_reconfigure(self, user_input=None) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors = {}
        if user_input:
            client = Client(user_input[CONF_HOST], user_input[CONF_PORT])
            try:
                info = await client.identify()
                if info.identity != entry.unique_id:
                    errors["base"] = "wrong_device"
                else:
                    return self.async_update_reload_and_abort(entry, data_updates=user_input)
            except RecircError:
                errors["base"] = "cannot_connect"
            finally:
                await client.close()
        return self.async_show_form(
            step_id="reconfigure",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=entry.data[CONF_HOST]): str,
                    vol.Required(CONF_PORT, default=entry.data[CONF_PORT]): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=65535)
                    ),
                }
            ),
        )


class SmartRecircOptionsFlow(OptionsFlow):
    """Select the physically installed flow meter for rate calibration."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title="", data=self.config_entry.options | user_input
            )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_FLOW_METER,
                        default=self.config_entry.options.get(
                            CONF_FLOW_METER, FLOW_METER_UNKNOWN
                        ),
                    ): vol.In(
                        {
                            FLOW_METER_UNKNOWN: "Unknown",
                            FLOW_METER_3_4: '3/4" stainless steel',
                            FLOW_METER_1: '1" brass',
                        }
                    ),
                }
            ),
        )
