from plugins.base_plugin.base_plugin import BasePlugin
from PIL import Image
import locale
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

        descimalSign = ","
        locale.setlocale(locale.LC_ALL, 'de_DE.utf8')
        amPm = "Uhr"
        currencySymbol = "€"

        cdt = datetime.now()

        batteryLevel = round(45, 0)
        batteryChargeAmount = 1256
        batteryCapacity = 9700

        solarMaxPower = 5500
        solarProductionToday = 6.82
        solarCurrentPower = 2300

        dapCurrentPrice = 0.305
        dapNextPrice = 0.295

        consumptionToday = 4.5

        renewableEnergyPercentage = 75
        renewableDescription = "Anteil EEG"

        chartMaxValue = 600
        chartValuesShown = 14
        chartData = [10,10,10,10,10,10,10,100,150,170,210,500,600,50,10,10,10,10,10,10,10,10,10,10]

        def replace_decimals(s1: str) -> str:
            if not isinstance(s1, str) :
                return s1
            return s1.replace(".", descimalSign)            

        data = {
            "solaredge_png": self.get_plugin_dir(f'icons/solaredge.png'),
            "star_png": self.get_plugin_dir(f'icons/star.png'),
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
            "dap": {    # DAP = Stock "Day Ahead Price" per kWh
                "icon": self.get_plugin_dir(f'icons/euro.png'),
                "currency_symbol": currencySymbol,
                "current_time": "11:00",
                "current_price": replace_decimals(f"{dapCurrentPrice:+}") + " " + currencySymbol,
                "next_time": "11:15",
                "next_price": replace_decimals(f"{dapNextPrice:+}") + " " + currencySymbol
            },
            "power_plant": {
                "icon": self.get_plugin_dir(f'icons/strommast.png'),
                "consumption_today": replace_decimals(str(consumptionToday)) + " kWh"
            },
            "current_date": {"week_day": cdt.strftime('%A'),
                             "day": cdt.strftime('%d'),
                             "month": cdt.strftime('%B'),
                             "time" : cdt.strftime('%H:%M'),
                             "am_pm" : amPm
                            },
            "chart": {
                "max_value": chartMaxValue,
                "values_shown": chartValuesShown,
                "data": chartData
            },
            "renewable": {
                "icon": self.get_plugin_dir(f'icons/leaf.png'),
                "description": renewableDescription,
                "percentage": str(round(renewableEnergyPercentage, 0)) + " %"
            }
        }

        return data
    