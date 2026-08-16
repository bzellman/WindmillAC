#coordinator.py
import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

class WindmillDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Windmill AC API."""

    def __init__(self, hass, blynk_service):
        """Initialize."""
        _LOGGER.debug("2Starting data from Windmill AC")
        self.blynk_service = blynk_service
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self):
        """Fetch data from Windmill AC."""
        _LOGGER.debug("Fetching data from Windmill AC")
        try:
            data = {
                "current_temp": await self.blynk_service.async_get_pin_value('V1'),
                "target_temp": await self.blynk_service.async_get_pin_value('V2'),
                "mode": await self.blynk_service.async_get_mode(),
                "fan": await self.blynk_service.async_get_fan(),
                "power": await self.blynk_service.async_get_power(),
            }
        except Exception as err:
            _LOGGER.error(f"Error fetching data: {err}")
            raise UpdateFailed(f"Error fetching data: {err}")

        # Power/energy are optional telemetry pins that aren't confirmed to
        # exist on every device/firmware. BlynkService already returns None
        # for them instead of raising, but fetch them outside the block
        # above and guard again here anyway: a failure here must only make
        # those two sensors unavailable, never take down the climate entity
        # or block setup.
        try:
            data["power_consumption"] = await self.blynk_service.async_get_power_consumption()
        except Exception as err:
            _LOGGER.warning(f"Error fetching power consumption: {err}")
            data["power_consumption"] = None

        try:
            data["energy"] = await self.blynk_service.async_get_energy()
        except Exception as err:
            _LOGGER.warning(f"Error fetching energy: {err}")
            data["energy"] = None

        _LOGGER.debug(f"Data fetched from Windmill AC: {data}")
        return data
