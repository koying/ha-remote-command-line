"""The command_line component."""

import logging
import subprocess
from homeassistant.const import CONF_COMMAND
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.exceptions import TemplateError
from homeassistant.helpers import template

from .const import CONF_COMMAND_TIMEOUT, CONF_SSH_HOST, CONF_SSH_KEY, CONF_SSH_USER

_LOGGER = logging.getLogger(__name__)


def call_shell_with_returncode(command, timeout):
    """Run a shell command with a timeout.

    If log_return_code is set to False, it will not print an error if a non-zero
    return code is returned.
    """
    try:
        subprocess.check_output(
            command, shell=True, timeout=timeout  # nosec # shell by design
        )
        return 0
    except subprocess.CalledProcessError as proc_exception:
        _LOGGER.error("Command failed: %s", command)
        return proc_exception.returncode
    except subprocess.TimeoutExpired:
        _LOGGER.error("Timeout for command: %s", command)
        return -1
    except subprocess.SubprocessError:
        _LOGGER.error("Error trying to exec command: %s", command)
        return -1


def call_shell_with_value(command, timeout):
    """Run a shell command with a timeout and return the output."""
    try:
        return_value = subprocess.check_output(
            command, shell=True, timeout=timeout  # nosec # shell by design
        )
        return return_value.strip().decode("utf-8")
    except subprocess.CalledProcessError:
        _LOGGER.error("Command failed: %s", command)
    except subprocess.TimeoutExpired:
        _LOGGER.error("Timeout for command: %s", command)
    except subprocess.SubprocessError:
        _LOGGER.error("Error trying to exec command: %s", command)

    return None


class CommandData:
    """The class for handling the data retrieval."""

    def __init__(self, hass, config, command):
        """Initialize the data object."""
        self.value = None
        self.hass = hass
        self.config = config
        self.command: template.Template = command
        if self.command and self.hass:
            self.command.hass = self.hass
        self.timeout = config.get(CONF_COMMAND_TIMEOUT)
        self.user = config.get(CONF_SSH_USER)
        self.host = config.get(CONF_SSH_HOST)
        self.key = config.get(CONF_SSH_KEY)

    def update(self, with_value):
        """Get the latest data with a shell command."""
        try:
            command = self.command.render()
        except TemplateError as ex:
            _LOGGER.exception("Error rendering command template: %s", ex)
            return None if with_value else -1

        if (not self.user and not self.host and not self.key):
            ssh_command = command
        else:
            escaped_command = command.replace('"', '\\"').replace("'", "''")
            command_key = ""
            command_target = ""
            command_user = self.user
            if self.key:
                command_key = f'-i {self.key}'
            if self.host:
                command_target = self.host
            else:
                    command_target = "172.17.0.1"

        ssh_command = f"ssh -4 -o ConnectTimeout=3 -o StrictHostKeyChecking=no {command_key} {command_user}@{command_target} '{escaped_command}'"

        _LOGGER.debug("Running command: %s", command)
        if with_value:
            self.value = call_shell_with_value(ssh_command, self.timeout)
        else:
            self.value = call_shell_with_returncode(ssh_command, self.timeout)

        return self.value
