import asyncio
import importlib.util
import logging
import sys
import traceback
import types
import unittest
from pathlib import Path

MODULE = "custom_components.windmillac.blynk_service"
PARENT = "custom_components.windmillac"
SOURCE = Path(__file__).resolve().parents[1] / "custom_components/windmillac/blynk_service.py"
TOKEN = "BLYNK_TOKEN_SENTINEL"
RESPONSE_SECRET = "REFLECTED_RESPONSE_SECRET"
MISSING = object()
MODULE_KEYS = (
    MODULE, "requests", "homeassistant", "homeassistant.components",
    "homeassistant.components.climate", "homeassistant.components.climate.const",
)
class Capture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)
class Hass:
    async def async_add_executor_job(self, callback, *args):
        return callback(*args)
class BlynkServiceLoggingTests(unittest.TestCase):
    def setUp(self):
        self.parent, self.child = logging.getLogger(PARENT), logging.getLogger(MODULE)
        self.logger_state = {
            logger: (logger.level, logger.disabled, logger.propagate, list(logger.handlers))
            for logger in (self.parent, self.child)
        }
        self.module_state = {name: sys.modules.get(name, MISSING) for name in MODULE_KEYS}
        self.addCleanup(self._restore)
        self.capture = Capture()
        self.parent.addHandler(self.capture)
        self.parent.disabled, self.parent.propagate = False, False
        self.child.setLevel(logging.NOTSET)
        self.child.disabled, self.child.propagate = False, True
        self.requests = self._install_import_doubles()

    def _restore(self):
        for name, original in self.module_state.items():
            if original is MISSING:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original
        for logger, (level, disabled, propagate, handlers) in self.logger_state.items():
            logger.setLevel(level)
            logger.disabled, logger.propagate, logger.handlers[:] = disabled, propagate, handlers

    def _install_import_doubles(self):
        requests = types.ModuleType("requests")

        class RequestException(Exception):
            pass

        requests.exceptions = types.SimpleNamespace(RequestException=RequestException)
        requests.get = None
        homeassistant, components, climate, const = (
            types.ModuleType(name)
            for name in (
                "homeassistant", "homeassistant.components",
                "homeassistant.components.climate", "homeassistant.components.climate.const",
            )
        )
        homeassistant.__path__ = components.__path__ = climate.__path__ = []
        const.HVACMode = types.SimpleNamespace(
            AUTO="auto", COOL="cool", FAN_ONLY="fan_only", OFF="off"
        )
        const.ClimateEntityFeature = object()
        homeassistant.components, components.climate, climate.const = components, climate, const
        sys.modules.update({
            "requests": requests, "homeassistant": homeassistant,
            "homeassistant.components": components, "homeassistant.components.climate": climate,
            "homeassistant.components.climate.const": const,
        })
        return requests

    def _load(self, parent_level):
        self.parent.setLevel(parent_level)
        self.child.setLevel(logging.NOTSET)
        sys.modules.pop(MODULE, None)
        spec = importlib.util.spec_from_file_location(MODULE, SOURCE)
        module = importlib.util.module_from_spec(spec)
        sys.modules[MODULE] = module
        spec.loader.exec_module(module)
        self.assertEqual(module.__name__, MODULE)
        return module

    def _service(self, parent_level):
        return self._load(parent_level).BlynkService(
            Hass(), "https://dashboard.windmillair.com", TOKEN
        )

    def _messages(self):
        return [record.getMessage() for record in self.capture.records if record.name == MODULE]

    def test_module_logger_inherits_parent_warning_and_suppresses_debug(self):
        service = self._service(logging.WARNING)
        self.requests.get = lambda url: types.SimpleNamespace(status_code=200, text="1")
        self.assertEqual(self.child.level, logging.NOTSET)
        self.assertEqual(self.child.getEffectiveLevel(), logging.WARNING)
        self.assertFalse(self.child.isEnabledFor(logging.DEBUG))
        self.assertEqual(asyncio.run(service.async_get_pin_value("V1")), 1)
        self.assertEqual(self._messages(), [])

    def test_pin_operations_preserve_requests_without_logging_secrets(self):
        service, urls = self._service(logging.DEBUG), []
        set_response = f" accepted {RESPONSE_SECRET} "

        def fake_get(url):
            urls.append(url)
            return types.SimpleNamespace(status_code=200, text="1" if url.endswith("&V1") else set_response)

        self.requests.get = fake_get
        self.assertEqual(asyncio.run(service.async_get_pin_value("V1")), 1)
        self.assertEqual(asyncio.run(service.async_set_pin_value("V2", "72")), set_response.strip())
        self.assertEqual(urls, [
            f"https://dashboard.windmillair.com/external/api/get?token={TOKEN}&V1",
            f"https://dashboard.windmillair.com/external/api/update?token={TOKEN}&V2=72",
        ])
        messages = self._messages()
        self.assertTrue(messages, "Expected safe Blynk debug diagnostics at parent DEBUG")
        self.assertTrue(any("Response Status Code: 200" in message for message in messages))
        unsafe = [message for message in messages if TOKEN in message or RESPONSE_SECRET in message]
        self.assertEqual(unsafe, [], "Blynk diagnostics must exclude constructed request URLs and raw response data")

    def test_request_exception_is_token_safe_and_suppresses_raw_context(self):
        service = self._service(logging.WARNING)

        def fail(url):
            raise self.requests.exceptions.RequestException(f"transport failed for {url}")

        self.requests.get = fail
        with self.assertRaises(Exception) as raised:
            asyncio.run(service.async_get_pin_value("V1"))
        error = raised.exception
        self.assertEqual(str(error), "Failed to get pin value for V1")
        self.assertIsNone(error.__cause__)
        self.assertTrue(error.__suppress_context__)
        self.assertNotIn(TOKEN, "".join(traceback.format_exception(error)))
        self.assertFalse(any(TOKEN in message for message in self._messages()))
