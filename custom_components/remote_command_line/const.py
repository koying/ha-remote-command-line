"""Allows to configure custom shell commands to turn a value for a sensor."""
from homeassistant.helpers.config_validation import (  # noqa: F401
    PLATFORM_SCHEMA,
)
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

CONF_COMMAND_TIMEOUT = "command_timeout"
DEFAULT_TIMEOUT = 15
DOMAIN = "remote_command_line"
PLATFORMS = ["binary_sensor", "cover", "sensor", "switch"]

CONF_SSH_USER = "ssh_user"
CONF_SSH_HOST = "ssh_host"
CONF_SSH_KEY = "ssh_key"
CONF_POLLING = "polling"

BASE_SSH_SCHEMA = {
        vol.Optional(CONF_SSH_USER): cv.string,
        vol.Optional(CONF_SSH_HOST): cv.string,
        vol.Optional(CONF_SSH_KEY): cv.string,
    }

BASE_SSH_PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(BASE_SSH_SCHEMA)
