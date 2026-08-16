import logging
from homeassistant.components.climate import ClimateEntity, ClimateEntityDescription
from homeassistant.components.climate.const import HVACMode, ClimateEntityFeature
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfTemperature, UnitOfPower, UnitOfEnergy, ATTR_TEMPERATURE
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


def _windmill_ac_device_info(coordinator) -> DeviceInfo:
    """Build the shared DeviceInfo so all entities for this AC group under one device."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{DOMAIN}_{coordinator.blynk_service.token}_windmill_AC")},
        name="Windmill AC",
        manufacturer="Windmill"
    )


class WindmillClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Windmill Climate device."""

    def __init__(self, coordinator, entity_description: ClimateEntityDescription):
        """Initialize the climate device."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_name = "Windmill Climate"
        self._attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
        self._attr_unique_id = f"{DOMAIN}_{coordinator.blynk_service.token}_{entity_description.key}"
        self._attr_device_info = _windmill_ac_device_info(coordinator)
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
        return f"{DOMAIN}_{self.coordinator.blynk_service.token}_{self.entity_description.key}"

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


class WindmillPowerSensor(CoordinatorEntity, SensorEntity):
    """Representation of the Windmill AC's instantaneous power draw."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entity_description):
        """Initialize the power sensor."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{DOMAIN}_{coordinator.blynk_service.token}_{entity_description.key}"
        self._attr_device_info = _windmill_ac_device_info(coordinator)

    @property
    def native_value(self):
        """Return the current power draw, in Watts."""
        return self.coordinator.data.get("power_consumption")


class WindmillEnergySensor(CoordinatorEntity, SensorEntity):
    """Representation of the Windmill AC's cumulative energy consumption."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator, entity_description):
        """Initialize the energy sensor."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{DOMAIN}_{coordinator.blynk_service.token}_{entity_description.key}"
        self._attr_device_info = _windmill_ac_device_info(coordinator)

    @property
    def native_value(self):
        """Return the cumulative energy consumption, in kWh."""
        return self.coordinator.data.get("energy")
