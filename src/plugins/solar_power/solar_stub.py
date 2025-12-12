import requests
from datetime import datetime, timedelta
from plugins.solar_power.solar_provider import SolarProvider
import pytz
import logging

logger = logging.getLogger(__name__)

class SolarStub(SolarProvider):
    def get_battery_data(self, replace_decimals_func):
        """
        Returns the battery dictionary.
        
        Args:
            battery_level: Current battery level as percentage (0-100)
            battery_charge_amount: Current charge amount in Wh
            battery_capacity: Total battery capacity in Wh
            replace_decimals_func: Function to replace decimal separator
            
        Returns:
            Dictionary containing battery data with icon, level, capacity, and current power
        """

        battery_level = round(45, 0)
        battery_charge_amount = 1256
        battery_capacity = 9700

        return {
            "icon": None,  # Will be set by caller
            "level": battery_level,
            "level_text": str(battery_level) + " %",
            "capacity": replace_decimals_func(str(round(battery_capacity/1000, 1)) + " kWh"),
            "current_power": replace_decimals_func(str(round(battery_charge_amount/1000, 1)) + " kWh")
        }

    def get_solar_data(self, replace_decimals_func):
        """
        Returns the solar dictionary.
        
        Args:
            replace_decimals_func: Function to replace decimal separator
            
        Returns:
            Dictionary containing solar data with icon, max_power, production_today, and current_power
        """
        
        solar_max_power = 5500
        solar_production_today = 6.82
        solar_current_power = 2300

        return {
            "icon": None,  # Will be set by caller
            "max_power": replace_decimals_func(str(round(solar_max_power/1000, 1))) + " kWp",
            "production_today": replace_decimals_func(str(round(solar_production_today, 1))) + " kWh",
            "current_power": replace_decimals_func(str(round(solar_current_power, 0))) + " W"
        }

    def get_power_plant_data(self, replace_decimals_func):
        """
        Returns the power plant dictionary.
        
        Args:
            replace_decimals_func: Function to replace decimal separator
            
        Returns:
            Dictionary containing power plant data with icon and consumption_today
        """
        
        consumption_today = 4.5

        return {
            "icon": None,  # Will be set by caller
            "consumption_today": replace_decimals_func(str(consumption_today)) + " kWh"
        }

    def get_chart_data(self):
        """
        Returns the chart dictionary.
        
        Returns:
            Dictionary containing chart data with max_value, values_shown, and data
        """
        
        chart_max_value = 600
        chart_values_shown = 14
        chart_data = [10,10,10,10,10,10,10,100,150,170,210,500,600,50,10,10,10,10,10,10,10,10,10,10]

        return {
            "max_value": chart_max_value,
            "values_shown": chart_values_shown,
            "data": chart_data
        }

    def get_dap_data(self, settings, currency_symbol, replace_decimals_func, bzn="DE-LU"):
        """
        Returns the DAP (Day Ahead Price) dictionary using live data from Energy-Charts API.
        
        Args:
            settings: Plugin settings dictionary
            currency_symbol: Currency symbol (e.g., "€")
            replace_decimals_func: Function to replace decimal separator
            bzn: Bidding zone (default: "DE-LU" for Germany/Luxembourg)
            
        Returns:
            Dictionary containing DAP data with current and next price
        """
        logger.warning("Using Stub No real data")
        return {
            "show": settings.get('showPriceData') == 'true',
            "icon": None,
            "currency_symbol": currency_symbol,
            "current_time": "09:00",
            "current_price": "0.123 $",
            "next_time": "09:15",
            "next_price": "0.234 $"
        }
        

    def get_renewable_data(self, settings, replace_decimals_func=None, country="de", description="Anteil EEG"):
        """
        Returns the renewable energy data dictionary using live data from Energy-Charts API.
        
        Args:
            settings: Plugin settings dictionary
            replace_decimals_func: Function to replace decimal separator (optional)
            country: Country code (default: "de" for Germany)
            description: Description text (default: "Anteil EEG")
            
        Returns:
            Dictionary containing renewable energy data
        """

        logger.warning("Using Stub No real data")
        percentage_str = "50%"
        
        return {
            "show": settings.get('dapCountry') == 'DE-LU',
            "icon": None,  # Will be set by caller
            "description": description,
            "percentage": percentage_str
        }
