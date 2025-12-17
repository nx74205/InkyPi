from plugins.base_plugin.base_plugin import BasePlugin
from PIL import Image
import locale
import logging
from datetime import datetime, timezone
import pytz
from io import BytesIO
import importlib

logger = logging.getLogger(__name__)

def _load_solar_provider(provider_class_name):
    """
    Dynamically loads a solar provider class based on the class name.
    
    Args:
        provider_class_name: Name of the provider class (e.g., "SolarStub", "SolarEdge")
        
    Returns:
        The provider class
        
    Raises:
        ImportError: If the module cannot be imported
        AttributeError: If the class cannot be found in the module
    """
    # Convert class name to module name (e.g., SolarStub -> solar_stub)
    module_name = ''.join(['_' + c.lower() if c.isupper() else c for c in provider_class_name]).lstrip('_')
    
    try:
        # Import the module dynamically
        module = importlib.import_module(f'plugins.solar_power.{module_name}')
        
        # Get the class from the module
        provider_class = getattr(module, provider_class_name)
        
        logger.info(f"Successfully loaded solar provider: {provider_class_name}")
        return provider_class
        
    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to load solar provider '{provider_class_name}': {e}")
        raise


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

        image = self.render_image(dimensions, "solar_power.html", "solar_power.css", template_params)

        if not image:
            raise RuntimeError("Failed to take screenshot, please check logs.")
            
        return image

    def parse_solar_data(self, settings):

        country = settings.get('language', 'en')
        provider_class_name = settings.get('solarProvider', 'SolarBase')
        display_icon = settings.get('displayIcon', 'solaredge')

        if country == "de":
            descimalSign = ","
            locale.setlocale(locale.LC_ALL, 'de_DE.utf8')
            currencySymbol = "€"
            renewableDescription = "Erneuerbare"
        else:
            descimalSign = "."
            locale.setlocale(locale.LC_ALL, 'en_US.utf8')
            currencySymbol = "$"
            renewableDescription = "Renewables"

        cdt = datetime.now()

        def replace_decimals(s1: str) -> str:
            if not isinstance(s1, str) :
                return s1
            return s1.replace(".", descimalSign)            

        # Load solar provider dynamically based on settings
        solar_provider = _getSolarProvider(provider_class_name)

        dap_data = solar_provider.get_dap_data(settings, currencySymbol, replace_decimals, bzn=settings.get('dapCountry', 'DE-LU'))        
        renewable_data = solar_provider.get_renewable_data(settings, replace_decimals, country="de", description=renewableDescription)        
        battery_data = solar_provider.get_battery_data(replace_decimals)        
        solar_data = solar_provider.get_solar_data(replace_decimals)        
        power_plant_data = solar_provider.get_power_plant_data(replace_decimals)
        
        power_plant_data["icon"] = self.get_plugin_dir(f'icons/strommast.png')
        dap_data["icon"] = self.get_plugin_dir(f'icons/euro.png')
        solar_data["icon"] = self.get_plugin_dir(f'icons/solarhaus.png')
        chart_data = solar_provider.get_chart_data()
        renewable_data["icon"] = self.get_plugin_dir(f'icons/leaf.png')
        battery_data["icon"] = self.get_plugin_dir(f'icons/battery-' + f'{int(round(battery_data["level"] / 10) * 10)}' + '.png')

        data = {
            "solarprovider_png": self.get_plugin_dir(f'icons/' + display_icon + '.png'),
            "star_png": self.get_plugin_dir(f'icons/star.png'),
            "dap": dap_data,
            "renewable": renewable_data,
            "battery": battery_data,
            "solar": solar_data,
            "power_plant": power_plant_data,
            "chart": chart_data,
            "current_date": {
                "week_day": cdt.strftime('%A'),
                "day": cdt.strftime('%d.'),
                "month": cdt.strftime('%B'),
                "time": cdt.strftime('%I:%M') if country == "en" else cdt.strftime('%H:%M'),
                "am_pm": cdt.strftime('%p') if country == "en" else ""
            }
        }

        return data

def _getSolarProvider(provider_class_name):
    try:
        provider_class = _load_solar_provider(provider_class_name)
        solar_provider = provider_class()

    except (ImportError, AttributeError) as e:
        logger.warning(f"Failed to load provider '{provider_class_name}', falling back to SolarStub: {e}")
        try:
            # Try to load SolarStub as fallback
            fallback_class = _load_solar_provider('SolarStub')
            solar_provider = fallback_class()
        except (ImportError, AttributeError) as fallback_error:
            logger.error(f"Failed to load SolarStub fallback: {fallback_error}")

    return solar_provider
        
        
    