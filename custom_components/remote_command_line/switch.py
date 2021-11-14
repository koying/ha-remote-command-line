"""Support for custom shell commands to turn a switch on/off."""
import logging

import voluptuous as vol

from homeassistant.components.switch import (
    ENTITY_ID_FORMAT,
    SwitchEntity,
)
from homeassistant.const import (
    CONF_COMMAND_OFF,
    CONF_COMMAND_ON,
    CONF_COMMAND_STATE,
    CONF_FRIENDLY_NAME,
    CONF_SWITCHES,
    CONF_VALUE_TEMPLATE,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.reload import setup_reload_service

from . import CommandData
from .const import BASE_SSH_PLATFORM_SCHEMA, CONF_COMMAND_TIMEOUT, CONF_POLLING, DEFAULT_TIMEOUT, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

SWITCH_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_COMMAND_OFF, default="true"): cv.template,
        vol.Optional(CONF_COMMAND_ON, default="true"): cv.template,
        vol.Optional(CONF_COMMAND_STATE, default=None): vol.Any(cv.template, None),
        vol.Optional(CONF_FRIENDLY_NAME): cv.string,
        vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
        vol.Optional(CONF_COMMAND_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
        vol.Optional(CONF_POLLING, default=True): cv.boolean,
    }
)

PLATFORM_SCHEMA = BASE_SSH_PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_SWITCHES): cv.schema_with_slug_keys(SWITCH_SCHEMA)}
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Find and return switches controlled by shell commands."""

    setup_reload_service(hass, DOMAIN, PLATFORMS)

    devices = config.get(CONF_SWITCHES, {})
    switches = []

    for object_id, device_config in devices.items():
        value_template = device_config.get(CONF_VALUE_TEMPLATE)

        if value_template is not None:
            value_template.hass = hass

        switches.append(
            CommandSwitch(
                hass,
                config,
                object_id,
                device_config.get(CONF_FRIENDLY_NAME, object_id),
                device_config[CONF_COMMAND_ON],
                device_config[CONF_COMMAND_OFF],
                device_config.get(CONF_COMMAND_STATE),
                value_template,
            )
        )

    if not switches:
        _LOGGER.error("No switches added")
        return False

    add_entities(switches)


class CommandSwitch(SwitchEntity):
    """Representation a switch that can be toggled using shell commands."""

    def __init__(
        self,
        hass,
        config,
        object_id,
        friendly_name,
        command_on,
        command_off,
        command_state,
        value_template,
    ):
        """Initialize the switch."""
        self._hass = hass
        self.entity_id = ENTITY_ID_FORMAT.format(object_id)
        self._name = friendly_name
        self._state = False
        self._command_on = CommandData(hass, config, command_on)
        self._command_off = CommandData(hass, config, command_off)
        if command_state:
            self._command_state = CommandData(hass, config, command_state)
        else:
            self._command_state = None
        self._value_template = value_template
        self._polling = config.get(CONF_POLLING)

    @classmethod
    def _switch(cls, command):
        """Execute the actual commands."""
        success = command.update(False) == 0

        if not success:
            _LOGGER.error("Command failed: %s", command)

        return success

    @property
    def should_poll(self):
        """Only poll if we have state command."""
        return (self._polling and self._command_state is not None)

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    @property
    def assumed_state(self):
        """Return true if we do optimistic updates."""
        return self._command_state is None

    def _query_state(self):
        """Query for state."""
        if self._value_template:
            return self._command_state.update(with_value=True)
        return self._command_state.update(with_value=False) == 0

    def update(self):
        """Update device state."""
        if self._command_state:
            payload = str(self._query_state())
            if self._value_template:
                payload = self._value_template.render_with_possible_json_value(payload)
            self._state = payload.lower() == "true"

    def turn_on(self, **kwargs):
        """Turn the device on."""
        if self._switch(self._command_on) and not self._command_state:
            self._state = True
            self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        if self._switch(self._command_off) and not self._command_state:
            self._state = False
            self.schedule_update_ha_state()
