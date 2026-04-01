import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Configurare senzori Aquatim fără CoordinatorEntity."""
    api_instance = hass.data["Aquatim"][entry.entry_id]
    
    # Executăm un update inițial pentru a avea date
    await api_instance.get_data()
    
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

class AquatimSensor(Entity, SensorEntity):
    """Reprezentarea unui senzor Aquatim ca entitate simplă."""

    def __init__(self, api, entry, key, name, icon, device_class, unit):
        """Inițializare senzor."""
        self._api = api
        self._entry = entry
        self._key = key
        
        self._attr_name = f"Aquatim {name}"
        self._attr_unique_id = f"aquatim_{entry.entry_id}_{key}"
        self._attr_icon = icon
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        
        if key == "sold":
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Returnează valoarea direct din instanța API."""
        # Presupunem că api.get_data() a fost deja rulat sau datele sunt stocate
        # Dacă ai implementat stocarea în self.data în api.py, folosim aia:
        if hasattr(self._api, "last_data") and self._api.last_data:
             return self._api.last_data.get(self._key)
        
        # Dacă api.py returnează datele direct din funcția get_data fără stocare internă,
        # va trebui să ne asigurăm că API-ul salvează undeva ultimul rezultat.
        return None

    async def async_update(self):
        """Update periodic al senzorului."""
        # Această metodă va rula periodic pentru a împrospăta datele
        data = await self._api.get_data()
        if data:
            # Salvăm datele în instanța API pentru ca toți senzorii să le poată citi
            self._api.last_data = data

    @property
    def device_info(self):
        """Grupare sub un singur dispozitiv."""
        return {
            "identifiers": {("Aquatim", self._entry.entry_id)},
            "name": "Portal Aquatim",
            "manufacturer": "Aquatim SA",
            "entry_type": "service",
        }