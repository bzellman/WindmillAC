import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, CONF_TOKEN

class WindmillConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Windmill integration."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return WindmillOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Windmill AC: Device Token", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_TOKEN): str,
        })

        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

class WindmillOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Windmill options."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Windmill AC: Device Token", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_TOKEN, default=self.config_entry.data.get(CONF_TOKEN)): str,
        })

        return self.async_show_form(
            step_id="init", data_schema=schema, errors=errors
        )
