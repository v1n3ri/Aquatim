import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Configurare senzori Aquatim."""
    # Verificăm ce avem în hass.data
    coordinator = hass.data["Aquatim"][entry.entry_id]
    
    # Definim lista de senzori
    sensors = [
        AquatimSensor(coordinator, entry, "nume", "Nume Client", "mdi:account"),
        AquatimSensor(coordinator, entry, "cod_client", "Cod Client", "mdi:identifier"),
        AquatimSensor(coordinator, entry, "nr_contract", "Număr Contract", "mdi:file-certificate"),
        AquatimSensor(coordinator, entry, "adresa", "Adresă Consum", "mdi:map-marker"),
        AquatimSensor(coordinator, entry, "stare", "Stare Contract", "mdi:check-circle"),
        AquatimSensor(coordinator, entry, "sold", "Sold Curent", "mdi:cash-register", SensorDeviceClass.MONETARY, "RON"),
        AquatimSensor(coordinator, entry, "perioada_index", "Status Perioadă Citire", "mdi:calendar-clock"),
        AquatimSensor(coordinator, entry, "start_citire", "Început Perioadă Citire", "mdi:calendar-arrow-right"),
        AquatimSensor(coordinator, entry, "sfarsit_citire", "Sfârșit Perioadă Citire", "mdi:calendar-arrow-left"),
    ]
    
    async_add_entities(sensors)

class AquatimSensor(CoordinatorEntity, SensorEntity):
    """Reprezentarea unui senzor Aquatim."""

    def __init__(self, coordinator, entry, key, name, icon, device_class=None, unit=None):
        """Inițializare senzor."""
        super().__init__(coordinator)
        self._key = key
        self._entry = entry
        self._attr_name = f"Aquatim {name}"
        # Folosim direct entry.entry_id pentru a evita AttributeError
        self._attr_unique_id = f"aquatim_{entry.entry_id}_{key}"
        self._attr_icon = icon
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        
        if key == "sold":
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Returnează valoarea din datele coordinatorului."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._key)

    @property
    def device_info(self):
        """Informații despre dispozitiv."""
        return {
            "identifiers": {("Aquatim", self._entry.entry_id)},
            "name": "Portal Aquatim",
            "manufacturer": "Aquatim SA",
            "entry_type": "service",
        }