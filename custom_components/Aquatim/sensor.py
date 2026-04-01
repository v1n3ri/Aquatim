import logging
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    api = hass.data[DOMAIN][entry.entry_id]

    async def async_update_data():
        return await api.get_data()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="aquatim_coordinator",
        update_method=async_update_data,
        update_interval=timedelta(hours=6),
    )

    await coordinator.async_config_entry_first_refresh()

    sensors = [
        AquatimSensor(coordinator, entry, "Cod Client", "cod_client", "mdi:account-badge"),
        AquatimSensor(coordinator, entry, "Numar Contract", "nr_contract", "mdi:file-certificate"),
        AquatimSensor(coordinator, entry, "Stare Contract", "stare", "mdi:check-circle"),
        AquatimSensor(coordinator, entry, "Adresa Furnizare", "adresa", "mdi:map-marker"),
    ]
    async_add_entities(sensors)

class AquatimSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry, name, key, icon):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"Aquatim {name}"
        self._attr_unique_id = f"aquatim_{entry.entry_id}_{key}"
        self._attr_icon = icon
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Aquatim Portal",
            "manufacturer": "Aquatim SA",
        }

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._key)