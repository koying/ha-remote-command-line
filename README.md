# Remote command_line integration for Home Assistant

This is an "extension" of the builtin [`command_line`](https://www.home-assistant.io/integrations/sensor.command_line/) integration.  
Besides the functionalities of the hereabove, it also:

- allow to disable polling altogether, relying on `homeassistant.update_entity` to trigger updates od the sensors
- has an help for remote connections via SSH

## Changelog

### 0.1

- Initial release

## Installation

### HACS

1. Launch HACS
1. Navigate to the Integrations section
1. "+ Explore & Add Repositories" button in the bottom-right
1. Search for "MQTT DiscoveryStream"
1. Select "Install this repository"
1. Restart Home Assistant

### Home Assistant

The integration is configured via YAML only.

Example:

```yaml
mqtt_discoverystream:
  base_topic: test_HA
  publish_attributes: false
  publish_timestamps: true
  publish_discovery: true
  include:
    entities:
      - sensor.owm_hourly_humidity
      - sensor.jellyfin_cloud
      - light.wled_esp
  exclude:
    entities:
      - sensor.plug_xiaomi_1_electrical_measurement
```

## Configuration

### Options

This integration can only be configuration via YAML.
The base options are the same as the command_line one. The additional options are:

| key      | default | required | description                                                                                  |
| -------- | ------- | -------- | -------------------------------------------------------------------------------------------- |
| polling  | true    | no       | Enable polling with `scan_interval` interval                                                 |
| ssh_user | no      | no       | User used when doing remote SSH connection                                                   |
| ssh_host | no      | no       | Host to SSH to. If not specified, defaults to `172.17.0.1`, which is usually the docker host |
| ssh_key  | no      | no       | Private key file used in SSH connections                                                     |

**NOTE:** If none of the ssh_* options is specified, the component do a local execution like `command_line`.

## Credits

- This custom component is based upon the `command_line` one from HA Core.  
