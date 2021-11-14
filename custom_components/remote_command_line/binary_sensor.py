"""Support for custom shell commands to retrieve values."""
from datetime import timedelta

import voluptuous as vol

from homeassistant.components.binary_sensor import (
    DEVICE_CLASSES_SCHEMA,
    BinarySensorEntity,
)
from homeassistant.const import (
    CONF_COMMAND,
    CONF_DEVICE_CLASS,
    CONF_NAME,
    CONF_PAYLOAD_OFF,
    CONF_PAYLOAD_ON,
    CONF_VALUE_TEMPLATE,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.reload import setup_reload_service

from . import CommandData
from .const import BASE_SSH_PLATFORM_SCHEMA, CONF_COMMAND_TIMEOUT, CONF_POLLING, DEFAULT_TIMEOUT, DOMAIN, PLATFORMS

DEFAULT_NAME = "Binary Command Sensor"
DEFAULT_PAYLOAD_ON = "ON"
DEFAULT_PAYLOAD_OFF = "OFF"

SCAN_INTERVAL = timedelta(seconds=60)


PLATFORM_SCHEMA = BASE_SSH_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_COMMAND): cv.template,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_PAYLOAD_OFF, default=DEFAULT_PAYLOAD_OFF): cv.string,
        vol.Optional(CONF_PAYLOAD_ON, default=DEFAULT_PAYLOAD_ON): cv.string,
        vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
        vol.Optional(CONF_COMMAND_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
        vol.Optional(CONF_POLLING, default=True): cv.boolean,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Command line Binary Sensor."""

    setup_reload_service(hass, DOMAIN, PLATFORMS)

    name = config.get(CONF_NAME)
    command = config.get(CONF_COMMAND)
    payload_off = config.get(CONF_PAYLOAD_OFF)
    payload_on = config.get(CONF_PAYLOAD_ON)
    device_class = config.get(CONF_DEVICE_CLASS)
    value_template = config.get(CONF_VALUE_TEMPLATE)
    if value_template is not None:
        value_template.hass = hass
    polling = config.get(CONF_POLLING)
    data = CommandData(hass, config, command)

    add_entities(
        [
            CommandBinarySensor(
                hass, data, name, device_class, payload_on, payload_off, value_template, polling
            )
        ],
        polling,
    )


class CommandBinarySensor(BinarySensorEntity):
    """Representation of a command line binary sensor."""

    def __init__(
        self, hass, data, name, device_class, payload_on, payload_off, value_template, polling
    ):
        """Initialize the Command line binary sensor."""
        self._hass = hass
        self.data = data
        self._attr_name = name
        self._attr_device_class = device_class
        self._state = False
        self._payload_on = payload_on
        self._payload_off = payload_off
        self._value_template = value_template
        self._attr_should_poll = polling

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._state

    def update(self):
        """Get the latest data and updates the state."""
        self.data.update(with_value=True)
        value = self.data.value

        if self._value_template is not None:
            value = self._value_template.render_with_possible_json_value(value, False)
        if value == self._payload_on:
            self._state = True
        elif value == self._payload_off:
            self._state = False
