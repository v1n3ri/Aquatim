import logging
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import config_validation as cv

from .api import AquatimAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Schema pentru serviciul de trimitere index
SERVICE_SEND_INDEX_SCHEMA = vol.Schema({
    vol.Required("value"): cv.string,
})

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configurarea integrării dintr-o intrare de configurare (Config Entry)."""
    
    email = entry.data["email"]
    password = entry.data["password"]

    # Inițializăm instanța API
    api = AquatimAPI(email, password)
    
    # Salvăm instanța API în hass.data pentru a fi accesibilă din sensor.py
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = api

    async def handle_send_water_index(call: ServiceCall):
        """Funcția care execută serviciul de transmitere index."""
        index_value = call.data.get("value")
        _LOGGER.info(f"Se încearcă trimiterea indexului {index_value} către Aquatim...")
        
        success = await api.send_index(index_value)
        
        if success:
            _LOGGER.info(f"Indexul {index_value} a fost transmis cu succes.")
            # Opțional: poți declanșa o notificare în interfața HA aici
        else:
            _LOGGER.error("Eroare la transmiterea indexului. Verifică log-urile API.")

    # Înregistrăm serviciul în Home Assistant
    # Acesta va apărea ca: aquatim.send_water_index
    hass.services.async_register(
        DOMAIN, 
        "send_water_index", 
        handle_send_water_index,
        schema=SERVICE_SEND_INDEX_SCHEMA
    )

    # Configurăm platformele asociate (în cazul tău, senzorii)
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Descărcarea integrării (când utilizatorul o șterge sau îi dă Disable)."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok