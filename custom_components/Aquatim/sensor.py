import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Configurarea senzorilor Aquatim și crearea dispozitivului."""
    api = hass.data[DOMAIN][entry.entry_id]

    async def async_update_data():
        """Metodă pentru refresh-ul datelor prin API."""
        # Aici apelăm noua metodă get_data() din api.py
        return await api.get_data()

    # Definim coordonatorul (update la fiecare 6 ore, datele de facturare nu se schimbă des)
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="aquatim_coordinator",
        update_method=async_update_data,
        update_interval=timedelta(hours=6),
    )

    # Primul refresh de date
    await coordinator.async_config_entry_first_refresh()

    # Definim lista de senzori pe care îi dorim
    sensors = [
        AquatimSensor(coordinator, entry, "Sold Curent", "sold", "RON", "mdi:cash-multiple", SensorDeviceClass.MONETARY),
        AquatimSensor(coordinator, entry, "Cod Client", "cod_client", None, "mdi:account-badge", None),
        AquatimSensor(coordinator, entry, "Numar Contract", "nr_contract", None, "mdi:file-document-outline", None),
        AquatimSensor(coordinator, entry, "Stare Contract", "stare", None, "mdi:check-decagram", None),
        AquatimSensor(coordinator, entry, "Nume Titular", "nume", None, "mdi:account", None),
    ]

    async_add_entities(sensors)

class AquatimSensor(CoordinatorEntity, SensorEntity):
    """Reprezentarea unui senzor Aquatim parte din dispozitivul central."""

    def __init__(self, coordinator, entry, name, key, unit, icon, device_class):
        """Inițializare senzor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"Aquatim {name}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_device_class = device_class
        
        # Dacă este soldul, îl setăm ca valoare numerică pentru grafice
        if key == "sold":
            self._attr_state_class = SensorStateClass.MEASUREMENT

        # Această secțiune creează "Device-ul" în Home Assistant
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Aquatim Portal",
            "manufacturer": "Aquatim SA",
            "model": self.coordinator.data.get("cod_client") if self.coordinator.data else "Client Aquatim",
            "configuration_url": "https://portal.aquatim.ro",
        }

    @property
    def native_value(self):
        """Returnează valoarea corespunzătoare cheii din dicționarul de date."""
        if self.coordinator.data is None:
            return None
        
        valoare = self.coordinator.data.get(self._key)
        
        # Conversie float pentru sold ca să meargă graficele
        if self._key == "sold" and valoare is not None:
            try:
                return float(valoare)
            except ValueError:
                return valoare
                
        return valoare

    @property
    def extra_state_attributes(self):
        """Adăugăm atribute suplimentare (ex: adresa pe senzorul de sold)."""
        if self._key == "sold" and self.coordinator.data:
            return {
                "adresa_furnizare": self.coordinator.data.get("adresa"),
                "cod_client": self