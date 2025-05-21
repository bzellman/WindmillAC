#climate.py

import logging
from homeassistant.components.climate import ClimateEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from .coordinator import WindmillDataUpdateCoordinator
from .entity import WindmillClimate

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


ENTITY_DESCRIPTIONS = [
    ClimateEntityDescription(
        key="windmill_AC",
        name="Windmill AC",
        icon="mdi:air-conditioner",
    ),
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Windmill AC climate entity."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities(
        WindmillClimate(
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )