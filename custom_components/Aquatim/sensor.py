import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import CURRENCY_EURO, UnitOfTime
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Configurare senzori Aquatim bazată pe Config Entry."""
    coordinator = hass.data["Aquatim"][entry.entry_id]
    
    # Definim lista de senzori pe care îi dorim în interfață
    sensors = [
        AquatimSensor(coordinator, "nume", "Nume Client", "mdi:account"),
        AquatimSensor(coordinator, "cod_client", "Cod Client", "mdi:identifier"),
        AquatimSensor(coordinator, "nr_contract", "Număr Contract", "mdi:file-certificate"),
        AquatimSensor(coordinator, "adresa", "Adresă Consum", "mdi:map-marker"),
        AquatimSensor(coordinator, "stare", "Stare Contract", "mdi:check-circle"),
        AquatimSensor(coordinator, "sold", "Sold Curent", "mdi:cash-register", SensorDeviceClass.MONETARY, "RON"),
        AquatimSensor(coordinator, "perioada_index", "Status Perioadă Citire", "mdi:calendar-clock"),
        AquatimSensor(coordinator, "start_citire", "Început Perioadă Citire", "mdi:calendar-arrow-right"),
        AquatimSensor(coordinator, "sfarsit_citire", "Sfârșit Perioadă Citire", "mdi:calendar-arrow-left"),
    ]
    
    async_add_entities(sensors)

class AquatimSensor(CoordinatorEntity, SensorEntity):
    """Reprezentarea unui senzor Aquatim."""

    def __init__(self, coordinator, key, name, icon, device_class=None, unit=None):
        """Inițializare senzor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"Aquatim {name}"
        self._attr_unique_id = f"aquatim_{coordinator.config_entry.entry_id}_{key}"
        self._attr_icon = icon
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        
        # Setăm clasa de stare pentru senzori numerici (Sold)
        if key == "sold":
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Returnează valoarea extrasă de API prin Coordinator."""
        if self.coordinator.data is None:
            return None
        
        # Extragem valoarea folosind cheia definită (ex: 'sold', 'start_citire')
        return self.coordinator.data.get(self._key)

    @property
    def device_info(self):
        """Grupăm toți senzorii sub același dispozitiv (Contractul Aquatim)."""
        return {
            "identifiers": {("Aquatim", self.coordinator.config_entry.entry_id)},
            "name": "Portal Aquatim",
            "manufacturer": "Aquatim SA",
            "model": self.coordinator.data.get("nr_contract", "Cont Client"),
        }