"""The command_line component."""
from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from homeassistant.const import CONF_COMMAND, CONF_NAME, CONF_TIMEOUT
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from pathlib import Path

from homeassistant.exceptions import TemplateError
from homeassistant.helpers import template
from datetime import datetime

from .const import (
    BASE_SSH_SCHEMA,
    CONF_COMMAND_TIMEOUT,
    CONF_SSH_HOST,
    CONF_SSH_KEY,
    CONF_SSH_USER,
    DEFAULT_TIMEOUT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

SERVICE_SCHEMA = vol.Schema(BASE_SSH_SCHEMA).extend(
    {
        vol.Required(CONF_COMMAND): cv.template,
        vol.Optional(CONF_COMMAND_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: cv.schema_with_slug_keys(SERVICE_SCHEMA)}, extra=vol.ALLOW_EXTRA
)


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
        return "Error: Command failed"
    except subprocess.TimeoutExpired:
        _LOGGER.error("Timeout for command: %s", command)
        return "Error: Timeout for command"
    except subprocess.SubprocessError:
        _LOGGER.error("Error trying to exec command: %s", command)
        return "Error trying to exec command"

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
        self.ssh_user = config.get(CONF_SSH_USER)
        self.ssh_host = config.get(CONF_SSH_HOST)
        self.ssh_key = config.get(CONF_SSH_KEY)

    def update(self, with_value):
        """Get the latest data with a shell command."""
        try:
            command = self.command.render()
        except TemplateError as ex:
            _LOGGER.exception("Error rendering command template: %s", ex)
            return None if with_value else -1

        if not self.ssh_user and not self.ssh_host and not self.ssh_key:
            ssh_command = command
        else:
            if not self.ssh_key:
                home = str(Path.home())
                if not os.path.isfile("/config/.ssh/id_rsa") and not os.path.isfile(
                    home + "/.ssh/id_rsa"
                ):
                    call_shell_with_value(
                        "mkdir /config/.ssh && ssh-keygen -q -b 2048 -t rsa -N '' -f /config/.ssh/id_rsa",
                        30,
                    )
                self.ssh_key = "/config/.ssh/id_rsa"
            escaped_command = command.replace("'", "''")
            command_key = ""
            command_target = ""
            command_user = self.ssh_user
            if self.ssh_key:
                command_key = f"-i {self.ssh_key}"
            if self.ssh_host:
                command_target = self.ssh_host
            else:
                command_target = "172.17.0.1"

            ssh_command = f"ssh -4 -o ConnectTimeout=3 -o StrictHostKeyChecking=no {command_key} {command_user}@{command_target} '{escaped_command}'"

        _LOGGER.debug("Running command: %s", command)
        if with_value:
            self.value = call_shell_with_value(ssh_command, self.timeout)
        else:
            self.value = call_shell_with_returncode(ssh_command, self.timeout)

        return self.value


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the remote_command_line component."""
    dom_conf = config.get(DOMAIN, {})

    async def async_service_handler(service: ServiceCall) -> None:
        """Execute a shell command service."""
        conf = dom_conf[service.service]
        timeout = (
            service.data[CONF_COMMAND_TIMEOUT]
            if CONF_COMMAND_TIMEOUT in service.data
            else conf[CONF_COMMAND_TIMEOUT]
        )

        try:
            cmd: template.Template = conf[CONF_COMMAND]
            if cmd and hass:
                cmd.hass = hass
            command = cmd.render()
        except TemplateError as ex:
            _LOGGER.exception("Error rendering command template: %s", ex)
            return
        ssh_user = conf.get(CONF_SSH_USER)
        ssh_host = conf.get(CONF_SSH_HOST)
        ssh_key = conf.get(CONF_SSH_KEY)
        if not ssh_user and not ssh_host and not ssh_key:
            ssh_command = command
        else:
            if not ssh_key:
                home = str(Path.home())
                if not os.path.isfile("/config/.ssh/id_rsa") and not os.path.isfile(
                    home + "/.ssh/id_rsa"
                ):
                    await hass.async_add_executor_job(
                        call_shell_with_value,
                        "mkdir /config/.ssh && ssh-keygen -q -b 2048 -t rsa -N '' -f /config/.ssh/id_rsa",
                        30,
                    )
                ssh_key = "/config/.ssh/id_rsa"
            escaped_command = command.replace("'", "''")
            command_key = ""
            command_target = ""
            command_user = ssh_user
            if ssh_key:
                command_key = f"-i {ssh_key}"
            if ssh_host:
                command_target = ssh_host
            else:
                command_target = "172.17.0.1"

            ssh_command = f"ssh -4 -o ConnectTimeout=3 -o StrictHostKeyChecking=no {command_key} {command_user}@{command_target} '{escaped_command}'"

        _LOGGER.debug("Running command: %s", command)
        ret = await hass.async_add_executor_job(
            call_shell_with_value, ssh_command, timeout
        )
        _LOGGER.debug("-- output: '%s'", ret)

    for name in dom_conf:
        hass.services.async_register(DOMAIN, name, async_service_handler)
    return True
