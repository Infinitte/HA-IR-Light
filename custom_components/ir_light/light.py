"""IR Controlled Light Plataform"""
import logging
import voluptuous as vol
import asyncio # for delay
from homeassistant.components.light import (
  ATTR_BRIGHTNESS,
  ATTR_COLOR_TEMP_KELVIN,
  ATTR_EFFECT,
  ATTR_HS_COLOR,
  ColorMode,
  LightEntity,
  LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry 
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType, StateType

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ir_light"
DEFAULT_NAME = "IR Light"

COLOR_CENTERS = {
  "color_red": 0,
  "color_orange": 30,
  "color_yellow": 60,
  "color_chartreuse": 90,
  "color_green": 120,
  "color_spring": 150,
  "color_cyan": 180,
  "color_azure": 210,
  "color_blue": 240,
  "color_violet": 270,
  "color_magenta": 300,
  "color_rose": 330,
}

async def async_setup_entry(
  hass: HomeAssistant,
  config_entry: ConfigEntry,
  async_add_entities: AddEntitiesCallback,
) -> None:
  """Configs IR light using Config Entry."""

  data = hass.data[DOMAIN][config_entry.entry_id]

  name = data.get(CONF_NAME)

  async_add_entities([IrLight(hass, name, data)], True)


COLOR_TEMP_CENTERS = {
  "ct_button_warm": 2700,
  "ct_button_natural": 4000,
  "ct_button_cool": 6500,
}


class IrLight(LightEntity):
  """IR Light class"""

  def __init__(self, hass: HomeAssistant, name: str, config_data: dict):
    """Constructor"""
    self.hass = hass
    self._name = name
    self._config_data = config_data

    self._is_color_temp_mode = config_data.get("light_mode") == "color_temperature"

    if self._is_color_temp_mode:
      self._attr_color_mode = ColorMode.COLOR_TEMP
      self._attr_supported_color_modes = {ColorMode.COLOR_TEMP}
      self._attr_min_color_temp_kelvin = 2700
      self._attr_max_color_temp_kelvin = 6500
    else:
      self._attr_color_mode = ColorMode.HS
      self._attr_supported_color_modes = {ColorMode.HS}

    # --- Persistent states ---
    self._state = False
    self._brightness = 255
    self._effect = None
    self._hs_color = None
    self._color_temp_kelvin: int | None = None
    self._color_steps = self._config_data.get("brightness_levels")

    self.button_map = {
      'ON': self._config_data.get('ir_button_on'),
      'OFF': self._config_data.get('ir_button_off'),
      'EFFECT_FLASH': self._config_data.get('ir_button_effect_flash'),
      'EFFECT_SMOOTH': self._config_data.get('ir_button_effect_smooth'),
      'BRIGHT_UP': self._config_data.get('ir_button_bright_up'),
      'BRIGHT_DOWN': self._config_data.get('ir_button_bright_down'),
    }

    self._effect_list = []
    if self.button_map.get('EFFECT_FLASH'):
      self._effect_list.append("Flash")
    if self.button_map.get('EFFECT_SMOOTH'):
      self._effect_list.append("Smooth")

    self._attr_supported_features = LightEntityFeature(0)
    if any(config_data.get(f"ir_button_effect_{e}") for e in ["flash", "smooth"]):
      self._attr_supported_features |= LightEntityFeature.EFFECT

  @property
  def name(self) -> str:
    return self._name

  @property
  def unique_id(self) -> str:
    return f"{DOMAIN}_{self._name.lower().replace(' ', '_')}"

  @property
  def is_on(self) -> bool:
    return self._state

  @property
  def brightness(self) -> int | None:
    """Returns brightness (0-255)"""
    return self._brightness

  #@property
  #def supported_features(self) -> int:
  #  features = SUPPORT_BRIGHTNESS | SUPPORT_COLOR
  #  if self._effect_list:
  #    features |= SUPPORT_EFFECT
  #    self._attr_supported_features = LightEntityFeature.EFFECT
  #  return features

  @property
  def effect_list(self) -> list[str] | None:
    return self._effect_list if self._effect_list else None

  @property
  def effect(self) -> str | None:
    return self._effect

  @property
  def hs_color(self) -> tuple[float, float] | None:
    return self._hs_color

  @property
  def color_temp_kelvin(self) -> int | None:
    return self._color_temp_kelvin

  async def _async_map_color_temp_to_button(self, kelvin: int) -> None:
    """Maps a color temperature in Kelvin to the closest configured IR button."""
    available = {
      key: center for key, center in COLOR_TEMP_CENTERS.items()
      if self._config_data.get(key)
    }
    if not available:
      return

    best_key = min(available, key=lambda k: abs(available[k] - kelvin))
    button_id = self._config_data.get(best_key)
    _LOGGER.debug(f"Color temp {kelvin}K → {best_key} ({available[best_key]}K)")
    await self._async_press_button(button_id)

  async def _async_map_color_to_button(self, hue: float, sat: float) -> None:
    """Color Selector Script"""

    button_id = None

    if sat < 10:
      button_id = self._config_data.get("color_white")
      if button_id:
        await self._async_press_button(button_id)
      return

    available_buttons = {}
    for key, center_hue in COLOR_CENTERS.items():
      b_id = self._config_data.get(key)
      if b_id:
        available_buttons[center_hue] = b_id

    best_button = None
    min_distance = 361

    for center_hue, b_id in available_buttons.items():
      distance = abs(hue - center_hue)
      if distance > 180:
        distance = 360 - distance

      if distance < min_distance:
        min_distance = distance
        best_button = b_id

    if best_button:
      _LOGGER.debug(f"Closest match for Hue {hue}: {best_button} (dist: {min_distance})")
      await self._async_press_button(best_button)

  async def _async_press_button(self, entity_id: str) -> None:
    """Helper to press the corresponding IR button."""

    if not entity_id or not isinstance(entity_id, str):
      _LOGGER.warning(f"Entity_id not found for action.")
      return

    domain = entity_id.split(".")[0]

    if domain == "button":
      service_domain = "button"
      service_name = "press"
    elif domain in ["scene", "script"]:
      service_domain = domain
      service_name = "turn_on"
    else:
      # Future prof
      service_domain = "homeassistant"
      service_name = "turn_on"
    
    await self.hass.services.async_call(
      service_domain,
      service_name,
      {"entity_id": entity_id},
      blocking=False
    )

  async def async_turn_on(self, **kwargs) -> None:
    """Turn on light. Manages brightness, color and effect"""

    # --- 1. Color Temperature Management (color_temp mode only) ---
    if ATTR_COLOR_TEMP_KELVIN in kwargs and self._is_color_temp_mode:
      self._color_temp_kelvin = kwargs[ATTR_COLOR_TEMP_KELVIN]

      if not self._state:
        await self._async_press_button(self.button_map.get('ON'))
        self._state = True
        await asyncio.sleep(0.5)

      await self._async_map_color_temp_to_button(self._color_temp_kelvin)

    # --- 2. HS Color Management (rgb mode) ---
    if ATTR_HS_COLOR in kwargs:
      self._hs_color = kwargs[ATTR_HS_COLOR]
      hue, sat = self._hs_color

      if not self._state or not kwargs:
        await self._async_press_button(self.button_map.get('ON'))
        self._state = True
        await asyncio.sleep(0.5)

      await self._async_map_color_to_button(hue, sat)

    # --- 3. Effect Management (set_effect) ---
    if ATTR_EFFECT in kwargs:
      effect = kwargs[ATTR_EFFECT]
      self._effect = effect

      if not self._state or not kwargs:
        await self._async_press_button(self.button_map.get('ON'))
        self._state = True
        await asyncio.sleep(0.5)

      await self._async_press_button(self.button_map.get(f"EFFECT_{effect.upper()}"))

    # --- 4. Brightness Management (set_level) ---
    if ATTR_BRIGHTNESS in kwargs:
      requested_brightness = kwargs[ATTR_BRIGHTNESS]

      target_ir_level = int(round((requested_brightness / 255) * self._color_steps))
      target_ir_level = max(0, min(self._color_steps, target_ir_level)) 
      current_ir_level = int(round((self._brightness / 255) * self._color_steps))

      # Replicar la lógica de pulsos de brillo (arriba/abajo)
      if target_ir_level == 0:
        await self._async_press_button(self.button_map.get('OFF'))
        self._state = False
        self._effect = None # Clean effect
        self.async_write_ha_state()
        return
      else:
        if not self._state or not kwargs:
          await self._async_press_button(self.button_map.get('ON'))
          self._state = True
          await asyncio.sleep(0.5)

        if target_ir_level != current_ir_level:
          diff = target_ir_level - current_ir_level

          action_key = 'BRIGHT_UP' if diff > 0 else 'BRIGHT_DOWN'

          # Executes brigthness change N times
          for _ in range(abs(diff)):
            await self._async_press_button(self.button_map.get(action_key))
            # Delay
            await asyncio.sleep(0.5)

        # Save new brightness (HA range)
        self._brightness = requested_brightness

    # --- 5. General switch (turn_on) ---
    # If nothing has change before or have changed but it was not ON
    if not self._state or not kwargs:
      await self._async_press_button(self.button_map.get('ON'))
      self._state = True

    self.async_write_ha_state()

  async def async_turn_off(self, **kwargs) -> None:
    """Turn off light"""
    await self._async_press_button(self.button_map.get('OFF'))
    self._state = False
    self._effect = None # Clean effect

    self.async_write_ha_state()

