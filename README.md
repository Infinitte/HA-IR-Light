# Home Assistant IR RGB Light Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![Downloads][download-latest-shield]]()
[![HACS Installs][hacs-installs-shield]]()
[![License][license-shield]](LICENSE)

# Home Assistant IR RGB Light Integration

This integration allows you to control "dumb" RGB LED lights (controlled via Infrared remotes) as if they were native smart lights in Home Assistant. It maps the **HS (Hue & Saturation) color wheel** and **Brightness** levels to specific IR button presses.

## ✨ Features
* **Native Color Wheel:** Select any color; the integration automatically calculates and presses the closest configured IR button using circular angular distance.
* **Proximity Mapping:** If you only have 4 buttons (Red, Green, Blue, White), selecting "Orange" on the UI will automatically trigger the "Red" IR command.
* **Adjustable Brightness Steps:** Define how many levels of brightness your remote supports (e.g., 5 steps or 10 steps) for accurate dimming.
* **Configurable Effects:** Map Home Assistant light effects (Flash, Smooth) to your remote's effect buttons.
* **Fully Configurable UI:** No YAML needed. Setup and reconfigure buttons directly via the Integrations dashboard.

## 🛠️ Installation

### HACS Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?category=Integration&repository=HA-IR-Light&owner=Infinitte)

Or Search for `IR RGB Light Mapper` in HACS and install it under the "Integrations" categroy.

- Restart Home Assistant
- In the HA UI go to Settings -> Integrations click "+ Add integration" and search for "IR RGB Light Mapper"
- Follow Configuration steps to create your first entity

### Manual Installation

<details>
<summary>More Details</summary>

- You should take the xxxx.zip file from the latest [published release](https://github.com/Infinitte/HA-IR-Light/releases).
- To install, place the contents of `custom_components` into the `<config directory>/custom_components` folder of your Home Assistant installation.
- Restart Home Assistant
- In the HA UI go to Settings -> Integrations click "+ Add integration" and search for "IR RGB Light Mapper"
- Follow Configuration steps to create your first entity
</details>

## ⚙️ Configuration
During setup, you will be asked for:
1.  **Basic Config:** Light name and mandatory IR buttons (On, Off, Brightness Up/Down).
2.  **Brightness Levels:** The number of presses it takes to go from min to max brightness (Default: 5).
3.  **Mandatory Colors:** Red, Green, Blue, and White buttons.
4.  **Optional Colors:** 9 additional color buttons (Orange, Yellow, Cyan, Magenta, etc.) to increase color accuracy.

## 📝 Requirements
* A working IR Bridge (Broadcom, ESPHome, etc.) that exposes buttons to Home Assistant.
* The IR buttons must be already configured as `button` entities in your system.

## ⚖️ License
MIT License

<!---->
[releases-shield]: https://img.shields.io/github/release/andrew-codechimp/HA-Battery-Notes.svg?style=for-the-badge
[releases]: https://github.com/Infinitte/HA-IR-Light/releases