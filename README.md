# Remote command-line integration for Home Assistant

This component brings together the builtin [`command_line`](https://www.home-assistant.io/integrations/sensor.command_line/) and [`shell command`](https://www.home-assistant.io/integrations/shell_command//) integrations.  
Besides the functionalities of the hereabove, it adds the following capabilities:

- allow to disable polling altogether, relying on `homeassistant.update_entity` to trigger updates of the sensors
- helper for remote connections via SSH
- adds a `timeout` parameter to the service

## Installation
### HACS

1. Launch HACS
1. Navigate to the Integrations section
1. Click the 3-dots and "Custom Repositories"
1. Add a new URL: "https://github.com/koying/ha-remote-command-line.git" with category "Integration"
1. "+ Explore & Add Repositories" button in the bottom-right
1. Search for "MQTT DiscoveryStream"
1. Select "Install this repository"
1. Restart Home Assistant

### Home Assistant

The integration is configured via YAML only.

Example of sensor:

```yaml
sensor:
  - platform: remote_command_line
    name: HA running version
    scan_interval:
      hours: 6
    command: >
      cat /config/.HA_VERSION
  - platform: remote_command_line
    name: HA image version
    scan_interval:
      days: 1
    ssh_user: user
    command: >
      IMAGE=`docker inspect home-assistant | jq -r '.[0].Config.Image'`; docker image inspect ${IMAGE} | jq -r '.[0].ContainerConfig.Labels["io.hass.version"]'
```

Example of service:

```yaml
remote_command_line:
  fetch_ha_image:
    ssh_user: user
    command_timeout: 900
    command: >
        IMAGE=`docker inspect home-assistant | jq -r '.[0].Config.Image'`; docker pull -q ${IMAGE}
```

## Configuration

### Options

This integration can only be configuration via YAML.
The base options are the same as the command_line one. The additional options are:

| key      | default                | required | description                                                                                    |
| -------- | ---------------------- | -------- | ---------------------------------------------------------------------------------------------- |
| polling  | true                   | no       | Enable polling with `scan_interval` interval                                                   |
| ssh_user | no                     | no       | User used when doing remote SSH connection                                                     |
| ssh_host | `host.docker.internal` | no       | Host to SSH to. If not specified, defaults to the docker host                                  |
| ssh_key  | `/config/.ssh/id_rsa`  | no       | Private key file used in SSH connections                                                       |

**NOTE:** If none of the ssh_* options is specified, the component do a local execution like `command_line`.

**NOTE 2:** If `ssh_user` or `ssh_host` is specified, but not `ssh_key`, and `/config/.ssh/id_rsa` does not exist, an SSH keypair will be automatically created in `/config/.ssh`.

**NOTE 2:** If a command doesn't produce any text, the current date/time is used as the state.
