"""Constants for Windmill AC."""
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

NAME = "WindmillAC"
DOMAIN = "windmillac"
VERSION = "1.1.0"
PLATFORMS = ["climate", "sensor"]
UPDATE_INTERVAL = 60
CONF_TOKEN = "token"
BASE_URL = "https://dashboard.windmillair.com"

# Power/energy telemetry pins, confirmed by probing a live device
# (Template Id TMPLRK32gafq, firmware 0.4.7). Not guaranteed to exist on
# every Windmill AC device/firmware/template, so failures reading these
# are treated as optional/best-effort rather than fatal (see
# coordinator.py and BlynkService._async_get_float_pin).
PIN_POWER_CONSUMPTION = "V15"
PIN_ENERGY = "V16"
