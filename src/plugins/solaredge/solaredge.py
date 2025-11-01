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

        DECIMAL_SIGN = ","

        def replace_decimals(s1: str) -> str:
            if not isinstance(s1, str) :
                return s1
            return s1.replace(".", DECIMAL_SIGN)

        cdt = datetime.now()

        batteryLevel = round(45, 0)
        batteryChargeAmount = 1256
        batteryCapacity = 9700

        solarMaxPower = 5500
        solarProductionToday = 6.82
        solarCurrentPower = 2300

        consumptionToday = 4.5
        
        currentSolarPower = 2500

        data = {
            "solaredge_png": self.get_plugin_dir(f'icons/solaredge.png'),
            "battery": {
                "icon": self.get_plugin_dir(f'icons/battery-' + f'{int(round(batteryLevel / 10) * 10)}' + '.png'),
                "level": str(batteryLevel) + " %",
                "capacity": replace_decimals(str(round(batteryCapacity/1000, 1)) + " kWh"),
                "current_power": replace_decimals(str(round(batteryChargeAmount/1000, 1)) + " kWh")
            },
            "solar": {
                "icon": self.get_plugin_dir(f'icons/solarhaus.png'),
                "max_power": replace_decimals(str(round(solarMaxPower/1000, 1))) + " kWp",
                "production_today": replace_decimals(str(round(solarProductionToday, 1))) + " kWh",
                "current_power": replace_decimals(str(round(solarCurrentPower, 0))) + " W"
            },
            
            #"solar_house_png": self.get_plugin_dir(f'icons/solarhaus.png'),
            "power_plant_png": self.get_plugin_dir(f'icons/strommast.png'),
            "euro_png": self.get_plugin_dir(f'icons/euro.png'),
            
            "consumption_today": replace_decimals(str(consumptionToday)) + " kWh",
            "current_power": str(currentSolarPower),
            "current_date": {"week_day": "Dienstag",
                             "day": "14.",
                             "month": "Oktober",
                             "time" : "12:00",
                             "am_pm" : "Uhr"
                            },
            "pv_production_max_value": 600,
            "pv_production_values_shown": 14,
            "pv_production_data": [10,10,10,10,10,10,10,100,150,170,210,500,600,50,100,10,10,10,10,10,10,10,10,10]
        }

        return data

