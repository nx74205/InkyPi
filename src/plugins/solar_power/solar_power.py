from plugins.base_plugin.base_plugin import BasePlugin
from plugins.solar_power.solar_base import SolarBase
from PIL import Image
import locale
import logging
from datetime import datetime, timezone
import pytz
from io import BytesIO

logger = logging.getLogger(__name__)

class SolarPower(BasePlugin):
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
            template_params = self.parse_solar_data(settings)
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

    def parse_solar_data(self, settings):

        country = settings.get('country', 'en')
        if country == "de":
            descimalSign = ","
            locale.setlocale(locale.LC_ALL, 'de_DE.utf8')
            amPm = "Uhr"
            currencySymbol = "€"
        else:
            descimalSign = "."
            locale.setlocale(locale.LC_ALL, 'en_US.utf8')
            amPm = ""
            currencySymbol = "$"

        cdt = datetime.now()

        renewableDescription = "Anteil EEG"

        def replace_decimals(s1: str) -> str:
            if not isinstance(s1, str) :
                return s1
            return s1.replace(".", descimalSign)            

        solar_base = SolarBase()
        
        dap_data = solar_base.get_dap_data(
            settings, 
            currencySymbol, 
            replace_decimals,
            bzn=settings.get('dapCountry', 'DE-LU')
        )
        
        renewable_data = solar_base.get_renewable_data(
            settings,
            replace_decimals,
            country="de",
            description=renewableDescription
        )
        
        battery_data = solar_base.get_battery_data(
            replace_decimals
        )
        
        solar_data = solar_base.get_solar_data(
            replace_decimals
        )
        
        power_plant_data = solar_base.get_power_plant_data(
            replace_decimals
        )
        
        power_plant_data["icon"] = self.get_plugin_dir(f'icons/strommast.png')
        dap_data["icon"] = self.get_plugin_dir(f'icons/euro.png')
        solar_data["icon"] = self.get_plugin_dir(f'icons/solarhaus.png')
        chart_data = solar_base.get_chart_data()
        renewable_data["icon"] = self.get_plugin_dir(f'icons/leaf.png')
        battery_data["icon"] = self.get_plugin_dir(f'icons/battery-' + f'{int(round(battery_data["level"] / 10) * 10)}' + '.png')

        data = {
            "solaredge_png": self.get_plugin_dir(f'icons/solaredge.png'),
            "star_png": self.get_plugin_dir(f'icons/star.png'),
            "dap": dap_data,
            "renewable": renewable_data,
            "battery": battery_data,
            "solar": solar_data,
            "power_plant": power_plant_data,
            "chart": chart_data,
            "current_date": {
                "week_day": cdt.strftime('%A'),
                "day": cdt.strftime('%d'),
                "month": cdt.strftime('%B'),
                "time": cdt.strftime('%I:%M') if country == "en" else cdt.strftime('%H:%M'),
                "am_pm": cdt.strftime('%p') if country == "en" else amPm
            }
        }

        return data
    