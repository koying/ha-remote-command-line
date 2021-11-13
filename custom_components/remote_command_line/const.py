"""Allows to configure custom shell commands to turn a value for a sensor."""
from homeassistant.helpers.config_validation import (  # noqa: F401
    PLATFORM_SCHEMA,
)
import voluptuous
import homeassistant.helpers.config_validation as cv

CONF_COMMAND_TIMEOUT = "command_timeout"
DEFAULT_TIMEOUT = 15
DOMAIN = "command_line"
PLATFORMS = ["binary_sensor", "cover", "sensor", "switch"]

CONF_SSH_USER = "ssh_user"
CONF_SSH_HOST = "ssh_host"
CONF_SSH_KEY = "ssh_key"
CONF_POLLING = "polling"

BASE_SSH_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        voluptuous.Required(CONF_SSH_USER): cv.string,
        voluptuous.Optional(CONF_SSH_HOST): cv.string,
        voluptuous.Optional(CONF_SSH_KEY): cv.string,
        voluptuous.Optional(CONF_POLLING): cv.boolean,
    }
)