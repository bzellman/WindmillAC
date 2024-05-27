import logging
from homeassistant.components.climate import ClimateEntity, ClimateEntityDescription
from homeassistant.components.climate.const import HVACMode, ClimateEntityFeature
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


class WindmillClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Windmill Climate device."""

    def __init__(self, coordinator, entity_description: ClimateEntityDescription):
        """Initialize the climate device."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_name = "Windmill Climate"
        self._attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
        self._attr_unique_id = f"{DOMAIN}_{entity_description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name= "Windmill AC",
            manufacturer="Windmill"
        )
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE |
            ClimateEntityFeature.FAN_MODE |
            ClimateEntityFeature.TURN_ON |
            ClimateEntityFeature.TURN_OFF
        )
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.COOL, HVACMode.AUTO, HVACMode.FAN_ONLY]
        self._attr_fan_modes = ["Low", "Medium", "High", "Auto"]
        self._hvac_mode = coordinator.data.get("mode")
        self._target_temperature = None
        self._fan_mode = None
        self._is_on = False
        self._enable_turn_on_off_backwards_compatibility = False
        _LOGGER.debug(f"Setup WindmillClimate entity: {self.entity_description.name}")

    @property
    def unique_id(self):
        """Return a unique ID for the entity."""
        return f"{DOMAIN}_{self.entity_description.key}"

    @property
    def name(self):
        """Return the name of the entity."""
        return self.entity_description.name

    @property
    def current_temperature(self):
        """Return the current temperature."""
        _LOGGER.debug("current_temperature property called")
        return self.coordinator.data.get("current_temp")

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self.coordinator.data.get("target_temp")

    @property
    def hvac_mode(self):
        """Return current operation mode."""
        _LOGGER.debug("hvac_mode property called")
        mode = self.coordinator.data.get("mode")
        _LOGGER.debug(f"mode {mode}")
        return self.coordinator.data.get("mode")

    @property
    def fan_mode(self):
        """Return the fan setting."""
        return self.coordinator.data.get("fan")

    @property
    def is_on(self):
        return self.coordinator.data.get("power")

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            await self.coordinator.blynk_service.async_set_target_temp(temperature)
            await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new operation mode."""
        if hvac_mode != HVACMode.OFF:
            if not self.coordinator.data.get("power"):
                await self.async_turn_on()
            await self.coordinator.blynk_service.async_set_mode(hvac_mode)
        else:
            await self.async_turn_off()
        await self.coordinator.async_request_refresh()

    async def async_set_fan_mode(self, fan_mode):
        """Set new fan mode."""
        await self.coordinator.blynk_service.async_set_fan(fan_mode)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self):
        """Turn on the device."""
        await self.coordinator.blynk_service.async_set_power(True)
        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()

    async def async_turn_off(self):
        """Turn off the device."""
        await self.coordinator.blynk_service.async_set_power(False)
        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()

    async def async_update(self):
        """Update the climate entity."""
        _LOGGER.debug("Executing async_update in WindmillClimate")
        await super().async_update()
        self._attr_target_temperature = self.coordinator.data.get("target_temp")
        self._attr_current_temperature = self.coordinator.data.get("current_temp")
        self._attr_hvac_mode = self.coordinator.data.get("mode")
        self._attr_fan_mode = self.coordinator.data.get("fan")
        self._attr_is_on = self.coordinator.data.get("power")
        _LOGGER.debug(f"Updated target temperature: {self._attr_target_temperature}")
        _LOGGER.debug(f"Updated current temperature: {self._attr_current_temperature}")
        _LOGGER.debug(f"Updated HVAC mode: {self._attr_hvac_mode}")
        _LOGGER.debug(f"Updated fan mode: {self._attr_fan_mode}")
        _LOGGER.debug(f"Updated power state: {self._attr_is_on}")
