import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Configurarea senzorilor Aquatim bazată pe Config Entry."""
    api = hass.data[DOMAIN][entry.entry_id]

    # Definim coordonatorul care va face update la date (ex: la fiecare 60 minute)
    # Nu e nevoie de update des pentru facturi/sold
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="aquatim_sensor",
        update_method=api.get_balance,
        update_interval=timedelta(minutes=60),
    )

    # Primul refresh de date la pornire
    await coordinator.async_config_entry_first_refresh()

    # Adăugăm entitățile în HA
    async_add_entities([
        AquatimSoldSensor(coordinator, entry),
    ])

class AquatimSoldSensor(CoordinatorEntity, SensorEntity):
    """Senzorul care afișează soldul curent."""

    def __init__(self, coordinator, entry):
        """Inițializare senzor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Aquatim Sold Curent"
        self._attr_unique_id = f"{entry.entry_id}_sold"
        self._attr_native_unit_of_measurement = "RON"
        self._attr_icon = "mdi:cash-multiple"

    @property
    def native_value(self):
        """Returnează valoarea extrasă de coordonator din api.py."""
        # Datele returnate de api.get_balance() sunt stocate în coordinator.data
        if self.coordinator.data is None:
            return None
        
        try:
            # Curățăm textul în caz că api.py returnează string (ex: "0.00")
            return float(self.coordinator.data)
        except (ValueError, TypeError):
            _LOGGER.error(f"Valoare invalidă primită pentru sold: {self.coordinator.data}")
            return None

    @property
    def extra_state_attributes(self):
        """Atribute suplimentare (opțional)."""
        return {
            "ultima_actualizare": self.coordinator.last_update_success_time,
            "cont_utilizator": self._entry.data["email"]
        }