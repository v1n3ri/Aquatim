import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .api import AquatimAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configurare de bază fără servicii care pot da erori."""
    email = entry.data["email"]
    password = entry.data["password"]

    api = AquatimAPI(email, password)
    
    hass.data.setdefault(DOMAIN, {sys})
    hass.data[DOMAIN][entry.entry_id] = api

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok