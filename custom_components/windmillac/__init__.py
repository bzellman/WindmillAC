import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS, CONF_TOKEN, BASE_URL
from .blynk_service import BlynkService
from .coordinator import WindmillDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Windmill AC from a config entry."""
    _LOGGER.debug("Setting up Windmill AC config entry")

    server = BASE_URL
    token = entry.data[CONF_TOKEN]

    blynk_service = BlynkService(hass, server, token)
    coordinator = WindmillDataUpdateCoordinator(hass, blynk_service)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    await coordinator.async_config_entry_first_refresh()

    # Forward the platforms for this config entry.
    # async_forward_entry_setups was deprecated; use async_setup_platforms instead.
    await hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
