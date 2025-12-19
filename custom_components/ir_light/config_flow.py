"""Config flow for IR Light Integration"""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import selector

_LOGGER = logging.getLogger(__name__)

class IrLightConfigFlow(config_entries.ConfigFlow, domain="ir_light"):
  """Config Flow Handler for IR Light"""

  VERSION = 1
  #CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

  def __init__(self):
    self._config_data = {}
    self._entity_filter = {"domain": ["button", "scene", "script"]}

  async def async_step_user(self, user_input=None) -> FlowResult:
    """Handles initial config (Main buttons)"""
    errors: dict = {}

    if user_input is not None:
      self._config_data.update(user_input)
      return await self.async_step_effects()

    fields = {
      vol.Required(CONF_NAME, default="IR Light"): str,
      vol.Required("brightness_levels", default=5): vol.All(vol.Coerce(int), vol.Range(min=2, max=20)),
      vol.Required("ir_button_on"): selector({"entity": {"filter": self._entity_filter}}),
      vol.Required("ir_button_off"): selector({"entity": {"filter": self._entity_filter}}),
      vol.Required("ir_button_bright_up"): selector({"entity": {"filter": self._entity_filter}}),
      vol.Required("ir_button_bright_down"): selector({"entity": {"filter": self._entity_filter}}),
    }

    return self.async_show_form(
      step_id="user",
      data_schema=vol.Schema(fields),
      errors=errors
    )

  async def async_step_effects(self, user_input=None) -> FlowResult:
    """Handles effects config (Buttons for effects)"""
    errors: dict = {}

    if user_input is not None:
      self._config_data.update(user_input)
      title = self._config_data[CONF_NAME]
      return await self.async_step_colors()

    effect_fields = {
      vol.Optional("ir_button_effect_flash"): selector({"entity": {"filter": self._entity_filter}}),
      vol.Optional("ir_button_effect_smooth"): selector({"entity": {"filter": self._entity_filter}}),
    }

    return self.async_show_form(
      step_id="effects",
      data_schema=vol.Schema(effect_fields),
      errors=errors
    )

  async def async_step_colors(self, user_input=None) -> FlowResult:
    """Step 3: Color Mapping (13 buttons)"""
    errors: dict = {}

    if user_input is not None:
      self._config_data.update(user_input)

      title = self._config_data[CONF_NAME]
      return self.async_create_entry(title=title, data=self._config_data)

    mandatory_colors = ["White", "Red", "Green", "Blue"]
    all_colors = [
      "White", "Red", "Green", "Blue", "Orange",
      "Yellow", "Chartreuse", "Spring", "Cyan", "Azure",
      "Violet", "Magenta", "Rose"
    ]
    color_fields = {}
    for color in all_colors:
      field_id = f"color_{color.lower()}"
      selector_config = selector({"entity": {"filter": self._entity_filter}})
      if color in mandatory_colors:
        color_fields[vol.Required(field_id)] = selector_config
      else:
        color_fields[vol.Optional(field_id)] = selector_config

    return self.async_show_form(
      step_id="colors",
      data_schema=vol.Schema(color_fields),
      description_placeholders={
        "Guide": "Use color wheel"
      },
      errors=errors
    )

  @staticmethod
  @callback
  def async_get_options_flow(config_entry):
    return IrLightOptionsFlowHandler(config_entry)

class IrLightOptionsFlowHandler(config_entries.OptionsFlow):

  def __init__(self, config_entry):
    super().__init__()
    self._config_entry = config_entry
    self._config_data = dict(config_entry.data)
    self._entity_filter = {"domain": ["button", "scene", "script"]}

  async def async_step_init(self, user_input=None):
    if user_input is not None:
      self._config_data.update(user_input)
      return await self.async_step_effects()

    fields = {
      vol.Required("brightness_levels", default=self._config_data.get("brightness_levels")): vol.All(vol.Coerce(int), vol.Range(min=2, max=20)),
      vol.Required("ir_button_on", default=self._config_data.get("ir_button_on")): selector({"entity": {"filter": self._entity_filter}}),
      vol.Required("ir_button_off", default=self._config_data.get("ir_button_off")): selector({"entity": {"filter": self._entity_filter}}),
      vol.Required("ir_button_bright_up", default=self._config_data.get("ir_button_bright_up")): selector({"entity": {"filter": self._entity_filter}}),
      vol.Required("ir_button_bright_down", default=self._config_data.get("ir_button_bright_down")): selector({"entity": {"filter": self._entity_filter}}),
    }
    return self.async_show_form(step_id="init", data_schema=vol.Schema(fields))

  async def async_step_effects(self, user_input=None):
    if user_input is not None:
      self._config_data.update(user_input)
      for key in ["ir_button_effect_flash", "ir_button_effect_smooth"]:
        if key not in user_input or user_input[key] in [None, "", "None"]:
          self._config_data.pop(key, None)

      return await self.async_step_colors()

    effect_fields  = {}
    for effect_key in ["ir_button_effect_flash", "ir_button_effect_smooth"]:
      effect_fields[vol.Optional(effect_key)] = selector({"entity": {"filter": self._entity_filter}})

    return self.async_show_form(
      step_id="effects",
      data_schema=self.add_suggested_values_to_schema(
        vol.Schema(effect_fields),
        self._config_data
      )
    )

  async def async_step_colors(self, user_input=None):
    if user_input is not None:
      self._config_data.update(user_input)

      all_color_keys = [
        f"color_{c.lower()}" for c in [
          "White", "Red", "Green", "Blue", "Orange",
          "Yellow", "Chartreuse", "Spring", "Cyan", "Azure",
          "Violet", "Magenta", "Rose"
        ]
      ]

      for key in all_color_keys:
        if key not in user_input or user_input[key] in [None, "", "None"]:
          self._config_data.pop(key, None)

      self.hass.config_entries.async_update_entry(
        self._config_entry, data=self._config_data
      )

      return self.async_create_entry(title="", data={})

    all_colors = [
      "White", "Red", "Green", "Blue", "Orange",
      "Yellow", "Chartreuse", "Spring", "Cyan", "Azure",
      "Violet", "Magenta", "Rose"
    ]
    
    mandatory = ["White", "Red", "Green", "Blue"]

    color_fields = {}
    for color in all_colors:
      field_id = f"color_{color.lower()}"
      if color in mandatory:
        color_fields[vol.Required(field_id)] = selector({"entity": {"filter": self._entity_filter}})
      else:
        color_fields[vol.Optional(field_id)] = selector({"entity": {"filter": self._entity_filter}})

    return self.async_show_form(
      step_id="colors", 
      data_schema=self.add_suggested_values_to_schema(
        vol.Schema(color_fields),
        self._config_data
      )
    )