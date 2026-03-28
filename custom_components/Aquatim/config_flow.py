import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD

class AquatimConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Aici s-ar putea adăuga o verificare a credențialelor înainte de salvare
            return self.async_create_entry(title=user_input[CONF_EMAIL], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors,
        )