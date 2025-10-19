from plugins.base_plugin.base_plugin import BasePlugin
from PIL import Image
import os
import requests
import logging
from datetime import datetime, timezone
import pytz
from io import BytesIO
import math

logger = logging.getLogger(__name__)

class Solaredge(BasePlugin):
    def generate_settings_template(self):
        template_params = super().generate_settings_template()
        template_params['api_key'] = {
            "required": True,
            "service": "SolarEdge",
            "expected_key": "SOLAREDGE_API_KEY"
        }
        template_params['style_settings'] = True
        return template_params

    def generate_image(self, settings, device_config):

        try:
            template_params = self.parse_solar_data()
            template_params['title'] = "Solarertrag"
            template_params["plugin_settings"] = settings

        except Exception as e:
            raise RuntimeError(f"please check logs.")
       
        dimensions = device_config.get_resolution()

        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        template_params["plugin_settings"] = settings

        image = self.render_image(dimensions, "solaredge.html", "solaredge.css", template_params)

        if not image:
            raise RuntimeError("Failed to take screenshot, please check logs.")
            
        return image

    def parse_solar_data(self):
        cdt = datetime.now()
        batteryLevel = 50
        consumptionToday = 4.5
        productionToday = 6.82
        currentPower = 1256

        data = {            
            "battery_png": self.get_plugin_dir(f'icons/{'battery-50'}.png'),
            "solaredge_png": self.get_plugin_dir(f'icons/solaredge.png'),
            "solar_house_png": self.get_plugin_dir(f'icons/solarhaus.png'),
            "power_plant_png": self.get_plugin_dir(f'icons/strommast.png'),
            "battery_level": str(batteryLevel) + " %",
            "battery_capacity": "10 kWh",
            "consumption_today": str(consumptionToday) + " kWh",
            "production_today": str(productionToday),
            "current_power": str(currentPower),
            "current_date": {"week_day": "Dienstag,",
                             "day": "14.",
                             "month": "Oktober",
                             "time" : "12:00",
                             "am_pm" : "UHR"
                            }
        }

        return data

