"""Allows to configure custom shell commands to turn a value for a sensor."""
from collections.abc import Mapping
from datetime import timedelta
import json
import logging

import voluptuous as vol

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (
    CONF_COMMAND,
    CONF_NAME,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_VALUE_TEMPLATE,
    STATE_UNKNOWN,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.reload import setup_reload_service

from . import CommandData
from .const import BASE_SSH_PLATFORM_SCHEMA, CONF_COMMAND_TIMEOUT, CONF_POLLING, DEFAULT_TIMEOUT, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

CONF_JSON_ATTRIBUTES = "json_attributes"

DEFAULT_NAME = "Command Sensor"

SCAN_INTERVAL = timedelta(seconds=60)

PLATFORM_SCHEMA = BASE_SSH_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_COMMAND): cv.template,
        vol.Optional(CONF_COMMAND_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
        vol.Optional(CONF_JSON_ATTRIBUTES): cv.ensure_list_csv,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
        vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
        vol.Optional(CONF_POLLING, default=True): cv.boolean,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Command Sensor."""

    setup_reload_service(hass, DOMAIN, PLATFORMS)

    name = config.get(CONF_NAME)
    command = config.get(CONF_COMMAND)
    unit = config.get(CONF_UNIT_OF_MEASUREMENT)
    value_template = config.get(CONF_VALUE_TEMPLATE)
    if value_template is not None:
        value_template.hass = hass
    json_attributes = config.get(CONF_JSON_ATTRIBUTES)
    polling = config.get(CONF_POLLING)
    data = CommandData(hass, config, command)
    _LOGGER.info("polling: " + ("yes" if polling else "no"))

    add_entities(
        [CommandSensor(hass, data, name, unit, value_template, json_attributes, polling)], polling
    )


class CommandSensor(SensorEntity):
    """Representation of a sensor that is using shell commands."""

    def __init__(
        self, hass, data, name, unit_of_measurement, value_template, json_attributes, polling
    ):
        """Initialize the sensor."""
        self._hass = hass
        self.data = data
        self._attr_extra_state_attributes = None
        self._json_attributes = json_attributes
        self._attr_name = name
        self._attr_native_value = None
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._value_template = value_template
        self._attr_should_poll = polling

    def update(self):
        """Get the latest data and updates the state."""
        value = self.data.update(with_value=True)

        if self._json_attributes:
            self._attr_extra_state_attributes = {}
            if value:
                try:
                    json_dict = json.loads(value)
                    if isinstance(json_dict, Mapping):
                        self._attr_extra_state_attributes = {
                            k: json_dict[k]
                            for k in self._json_attributes
                            if k in json_dict
                        }
                    else:
                        _LOGGER.warning("JSON result was not a dictionary")
                except ValueError:
                    _LOGGER.warning("Unable to parse output as JSON: %s", value)
            else:
                _LOGGER.warning("Empty reply found when expecting JSON data")

        if value is None:
            value = STATE_UNKNOWN
        elif self._value_template is not None:
            self._attr_native_value = self._value_template.render_with_possible_json_value(
                value, STATE_UNKNOWN
            )
        else:
            self._attr_native_value = value

        return self._attr_native_value
