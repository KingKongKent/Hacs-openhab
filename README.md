# openHAB Integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]
![][maintenance-shield]

_Component to integrate with [openHAB][openHAB]._

> **Note:** This is a fork of [kubawolanin/ha-openhab](https://github.com/kubawolanin/ha-openhab) updated for compatibility with Home Assistant 2024.x and later.

## Requirements

- Home Assistant 2024.1.0 or later
- openHAB 3.x or 4.x

## Supported Platforms

| Platform         | Item types                     | Description                              |
| ---------------- | ------------------------------ | ---------------------------------------- |
| `climate`        | `Group` (thermostats)          | Full thermostat control with temperature dial |
| `binary_sensor`  | `Contact`                      | Door/window sensors                      |
| `sensor`         | `String`, `Number`, `DateTime` | Read-only values                         |
| `number`         | `Number:Temperature`           | Controllable temperature setpoints       |
| `select`         | `String` (with options)        | Mode selection (Manual, Schedule, etc.)  |
| `switch`         | `Switch`                       | On/off switches                          |
| `cover`          | `Rollershutter`                | Blinds/shutters                          |
| `device_tracker` | `Location`                     | GPS tracking                             |
| `light`          | `Color`, `Dimmer`              | Lights with color/brightness             |
| `media_player`   | `Player`                       | Media controls                           |

## Features

### Climate/Thermostat Support
- Full climate entity with temperature dial UI (like MELCloud, Tado, etc.)
- Mode-based temperature control (Manual, Schedule, Away, Vacation, Frost Protection)
- Automatic temperature setpoint selection based on current mode
- Preset modes dynamically generated from openHAB command options
- Works with Danfoss and similar smart thermostats

### Device Grouping
- Entities are automatically grouped by openHAB Groups
- Thermostats appear as a single device with all related entities
- Clean device organization in Home Assistant

### Authentication
- Supports API token authentication
- Compatible with openHAB 4.x security model

## Installation

### HACS (Recommended)

1. Go to HACS → Integrations
2. Click the three dots menu → Custom repositories
3. Add `https://github.com/KingKongKent/Hacs-openhab` as an Integration
4. Search for "openHAB" and download
5. Restart Home Assistant
6. Go to Settings → Devices & Services → Add Integration → openHAB

### Manual Installation

1. Download the `custom_components/openhab/` folder from this repository
2. Copy it to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant
4. Add the integration via Settings → Devices & Services → Add Integration → openHAB

## Configuration

Configuration is done entirely through the UI. You will need:
- Your openHAB server URL (e.g., `http://192.168.1.100:8080`)
- An API token (create one in openHAB: Settings → API Security)

## Icons & Device Classes

- Icons are automatically assigned based on openHAB Item categories (Material Design Icons)
- Device classes are determined dynamically from Item names and labels
- Supports the openHAB classic iconset mapping

## Updating Items

When you add or remove Items in openHAB, reload the integration in Home Assistant to discover new entities.

## Contributions

Contributions are welcome! This is a community-maintained fork.

## Credits

Based on the original work by [Kuba Wolanin](https://github.com/kubawolanin/ha-openhab).

---

[openhab]: https://openhab.org
[commits-shield]: https://img.shields.io/github/commit-activity/y/KingKongKent/Hacs-openhab.svg?style=for-the-badge
[commits]: https://github.com/KingKongKent/Hacs-openhab/commits/master
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/KingKongKent/Hacs-openhab.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-KingKongKent-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/KingKongKent/Hacs-openhab.svg?style=for-the-badge
[releases]: https://github.com/KingKongKent/Hacs-openhab/releases
