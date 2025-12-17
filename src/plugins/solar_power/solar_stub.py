import requests
from datetime import datetime, timedelta
from plugins.solar_power.solar_provider import SolarProvider
import logging

logger = logging.getLogger(__name__)

class SolarStub(SolarProvider):
    # Stub default values
    DEFAULT_BATTERY_LEVEL = 0
    DEFAULT_BATTERY_CHARGED = 1500
    DEFAULT_BATTERY_DISCHARGED = 2000
    DEFAULT_BATTERY_CAPACITY = 9700
    DEFAULT_SOLAR_MAX_POWER = 5500
    DEFAULT_SOLAR_PRODUCTION = 6.82
    DEFAULT_SOLAR_CURRENT = 2300
    DEFAULT_CONSUMPTION = 4.5
    DEFAULT_CHART_MAX = 600
    DEFAULT_CHART_VALUES = 14
    # 24-hour chart data (hourly values in W)
    DEFAULT_CHART_DATA = [10,10,10,10,10,10,10,100,150,170,210,500,600,50,10,10,10,10,10,10,10,10,10,10]
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

        battery_level = self.DEFAULT_BATTERY_LEVEL
        battery_charged = self.DEFAULT_BATTERY_CHARGED
        battery_discharged = self.DEFAULT_BATTERY_DISCHARGED
        battery_capacity = self.DEFAULT_BATTERY_CAPACITY

        return {
            "icon": None,  # Will be set by caller
            "level": battery_level,
            "level_text": str(battery_level) + " %",
            "capacity": replace_decimals_func(str(round(battery_capacity/1000, 1)) + " kWh"),
            "current_power": f"+{replace_decimals_func(str(round(battery_charged/1000, 1)))} kWh/-{replace_decimals_func(str(round(battery_discharged/1000, 1)))} kWh"
        }

    def get_solar_data(self, replace_decimals_func):
        """
        Returns the solar dictionary.
        
        Args:
            replace_decimals_func: Function to replace decimal separator
            
        Returns:
            Dictionary containing solar data with icon, max_power, production_today, and current_power
        """
        
        solar_max_power = self.DEFAULT_SOLAR_MAX_POWER
        solar_production_today = self.DEFAULT_SOLAR_PRODUCTION
        solar_current_power = self.DEFAULT_SOLAR_CURRENT

        return {
            "icon": None,  # Will be set by caller
            "max_power": replace_decimals_func(str(round(solar_max_power/1000, 1))) + " kWp",
            "production_today": replace_decimals_func(str(round(solar_production_today, 1))) + " kWh",
            "current_power": str(int(round(solar_current_power))) + " W"
        }

    def get_power_plant_data(self, replace_decimals_func):
        """
        Returns the power plant dictionary.
        
        Args:
            replace_decimals_func: Function to replace decimal separator
            
        Returns:
            Dictionary containing power plant data with icon and consumption_today
        """
        
        consumption_today = self.DEFAULT_CONSUMPTION

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
        
        chart_max_value = self.DEFAULT_CHART_MAX
        chart_values_shown = self.DEFAULT_CHART_VALUES
        chart_data = self.DEFAULT_CHART_DATA

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
            "current_price": replace_decimals_func("0.123 ") + currency_symbol,
            "next_time": "09:15",
            "next_price": replace_decimals_func("0.234 ") + currency_symbol
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
