#sensor.py

import logging
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from .coordinator import WindmillDataUpdateCoordinator
from .entity import WindmillPowerSensor, WindmillEnergySensor

_LOGGER = logging.getLogger(__name__)


ENTITY_DESCRIPTIONS = [
    (
        SensorEntityDescription(
            key="windmill_AC_power",
            name="Windmill AC Power Consumption",
            icon="mdi:flash",
        ),
        WindmillPowerSensor,
    ),
    (
        SensorEntityDescription(
            key="windmill_AC_energy",
            name="Windmill AC Energy Consumption",
            icon="mdi:lightning-bolt",
        ),
        WindmillEnergySensor,
    ),
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Windmill AC sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities(
        entity_class(coordinator=coordinator, entity_description=entity_description)
        for entity_description, entity_class in ENTITY_DESCRIPTIONS
    )
