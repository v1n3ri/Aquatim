import logging
from datetime import timedelta
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=4)

async def async_setup_entry(hass, entry, async_add_entities):
    """Configurare senzori Aquatim."""
    api_instance = hass.data["Aquatim"][entry.entry_id]
    
    sensor_definitions = [
        ("nume", "Nume Client", "mdi:account", None, None),
        ("cod_client", "Cod Client", "mdi:identifier", None, None),
        ("nr_contract", "Număr Contract", "mdi:file-certificate", None, None),
        ("adresa", "Adresă Consum", "mdi:map-marker", None, None),
        ("stare", "Stare Contract", "mdi:check-circle", None, None),
        ("sold", "Sold Curent", "mdi:cash-register", SensorDeviceClass.MONETARY, "RON"),
        ("perioada_index", "Status Perioadă Citire", "mdi:calendar-clock", None, None),
        ("start_citire", "Început Perioadă Citire", "mdi:calendar-arrow-right", None, None),
        ("sfarsit_citire", "Sfârșit Perioadă Citire", "mdi:calendar-arrow-left", None, None),
    ]
    
    sensors = []
    for key, name, icon, device_class, unit in sensor_definitions:
        sensors.append(
            AquatimSensor(api_instance, entry, key, name, icon, device_class, unit)
        )
    
    async_add_entities(sensors, True)

class AquatimSensor(SensorEntity):
    """Reprezentarea unui senzor Aquatim."""

    def __init__(self, api, entry, key, name, icon, device_class, unit):
        """Inițializare senzor."""
        self._api = api
        self._entry = entry
        self._key = key
        
        self._attr_name = name 
        self._attr_unique_id = f"aquatim_{entry.entry_id}_{key}"
        self._attr_icon = icon
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        
        if key == "sold":
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Returnează valoarea din cache."""
        if hasattr(self._api, "last_data") and self._api.last_data:
             return self._api.last_data.get(self._key)
        return None

    async def async_update(self):
        """Update periodic."""
        data = await self._api.get_data()
        if data:
            self._api.last_data = data

    @property
    def device_info(self):
        """Grupare sub adresa de consum, nu sub un nume generic."""
        # Extragem adresa din cache-ul API-ului
        address = "Aquatim Portal"
        if hasattr(self._api, "last_data") and self._api.last_data:
            address = self._api.last_data.get("adresa", "Aquatim Portal")

        return {
            "identifiers": {("Aquatim", self._entry.entry_id)},
            "name": address,  # Aici punem adresa (ex: VIORELELOR, nr. 15)
            "manufacturer": "Aquatim SA",
            "entry_type": "service",
        }