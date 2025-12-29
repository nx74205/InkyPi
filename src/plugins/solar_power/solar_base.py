import requests
from datetime import datetime, timedelta
from plugins.solar_power.solar_provider import SolarProvider
from plugins.solar_power.dap_data_provider import DapDataProvider
import pytz
import logging

logger = logging.getLogger(__name__)

class SolarBase(SolarProvider):
    # Base URL configuration
    API_BASE_URL = 'http://192.168.0.140:8485/api/solar'
    
    # API endpoints
    BATTERY_SOC_URL = f'{API_BASE_URL}/battery-soc/current'
    BATTERY_DISCHARGED_URL = f'{API_BASE_URL}/battery/discharged'
    BATTERY_CHARGED_URL = f'{API_BASE_URL}/battery/charged'
    SOLAR_AC_OUT_SUMMARY_URL = f'{API_BASE_URL}/ac-out/summary'
    SOLAR_CURRENT_POWER_URL = f'{API_BASE_URL}/ac-out/currentPower'
    GRID_IMPORT_URL = f'{API_BASE_URL}/grid/import'
    GRID_EXPORT_URL = f'{API_BASE_URL}/grid/export'
    
    # Configuration constants
    SOLAR_MAX_POWER = 4400
    BATTERY_CAPACITY = 9700
    API_TIMEOUT = 5
    CHART_VALUES_SHOWN = 14
    DEFAULT_CHART_HOURS = 24
    
    # Fallback values
    DEFAULT_BATTERY_LEVEL = 45
    DEFAULT_BATTERY_CHARGED = 2589.0
    DEFAULT_BATTERY_DISCHARGED = 1256.0
    DEFAULT_SOLAR_PRODUCTION = 6820.0
    DEFAULT_SOLAR_CURRENT = 2300.0
    DEFAULT_GRID_IMPORT = 4500.0
    DEFAULT_GRID_EXPORT = 3200.0
    
    def __init__(self):
        """Initialize SolarBase with DAP data provider."""
        self.dap_provider = DapDataProvider()
    
    def _get_today_str(self):
        """Returns today's date as string in YYYY-MM-DD format."""
        return datetime.now().strftime('%Y-%m-%d')
    
    def _wh_to_kwh(self, wh_value, decimals=1):
        """Convert Watt-hours to Kilowatt-hours with rounding."""
        return round(wh_value / 1000, decimals)
    
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

        # Fetch battery level from API
        battery_level = self._fetch_battery_soc()
        
        # Fetch battery charged/discharged from API
        today = self._get_today_str()
        battery_charged = self._fetch_battery_charged(today)
        battery_discharged = self._fetch_battery_discharged(today)

        return {
            "icon": None,  # Will be set by caller
            "level": battery_level,
            "level_text": str(battery_level) + " %",
            "capacity": replace_decimals_func(str(self._wh_to_kwh(self.BATTERY_CAPACITY)) + " kWh"),
            "current_power": f"+{replace_decimals_func(str(self._wh_to_kwh(battery_charged)))} kWh/-{replace_decimals_func(str(self._wh_to_kwh(battery_discharged)))} kWh"
        }

    def get_solar_data(self, replace_decimals_func):
        """
        Returns the solar dictionary.
        
        Args:
            replace_decimals_func: Function to replace decimal separator
            
        Returns:
            Dictionary containing solar data with icon, max_power, production_today, and current_power
        """        

        # Fetch solar production from API
        today = self._get_today_str()
        solar_production_today = self._fetch_solar_production(today)
        
        # Fetch current solar power from API
        solar_current_power = self._fetch_solar_current_power()

        return {
            "icon": None,  # Will be set by caller
            "max_power": replace_decimals_func(str(self._wh_to_kwh(self.SOLAR_MAX_POWER))) + " kWp",
            "production_today": replace_decimals_func(str(self._wh_to_kwh(solar_production_today))) + " kWh",
            "current_power": str(int(round(solar_current_power))) + " W"
        }

    def get_power_plant_data(self, replace_decimals_func):
        """
        Returns the power plant dictionary.
        
        Args:
            replace_decimals_func: Function to replace decimal separator
            
        Returns:
            Dictionary containing power plant data with icon, consumption_today, and production_today
        """
        
        # Fetch grid import and export from API
        today = self._get_today_str()
        consumption_today = self._fetch_grid_import(today)
        production_today = self._fetch_grid_export(today)
        grid_balance = consumption_today - production_today

        return {
            "icon": None,  # Will be set by caller
            "consumption_today": replace_decimals_func(str(self._wh_to_kwh(consumption_today))) + " kWh",
            "production_today": replace_decimals_func(str(self._wh_to_kwh(production_today))) + " kWh",
            "grid_balance": replace_decimals_func(str(self._wh_to_kwh(grid_balance))) + " kWh"

        }

    def get_chart_data(self):
        """
        Returns the chart dictionary.
        
        Returns:
            Dictionary containing chart data with max_value, values_shown, and data
        """
        
        # Fetch chart data from API
        today = self._get_today_str()
        chart_data = self._fetch_solar_pv_chart_data(today)

        return {
            "max_value": self.SOLAR_MAX_POWER,
            "values_shown": self.CHART_VALUES_SHOWN,
            "data": chart_data
        }

    def get_dap_data(self, settings, currency_symbol, replace_decimals_func, bzn="DE-LU"):
        """
        Returns the DAP (Day Ahead Price) dictionary using live data from Energy-Charts API.
        Delegates to DapDataProvider.
        
        Args:
            settings: Plugin settings dictionary
            currency_symbol: Currency symbol (e.g., "€")
            replace_decimals_func: Function to replace decimal separator
            bzn: Bidding zone (default: "DE-LU" for Germany/Luxembourg)
            
        Returns:
            Dictionary containing DAP data with current and next price
        """
        return self.dap_provider.get_dap_data(settings, currency_symbol, replace_decimals_func, bzn)

    def get_renewable_data(self, settings, replace_decimals_func=None, country="de", description="Anteil EEG"):
        """
        Returns the renewable energy data dictionary using live data from Energy-Charts API.
        Delegates to DapDataProvider.
        
        Args:
            settings: Plugin settings dictionary
            replace_decimals_func: Function to replace decimal separator (optional)
            country: Country code (default: "de" for Germany)
            description: Description text (default: "Anteil EEG")
            
        Returns:
            Dictionary containing renewable energy data
        """
        return self.dap_provider.get_renewable_data(settings, replace_decimals_func, country, description)
    def _fetch_battery_soc(self):
        """
        Fetches the current battery state of charge (SOC) from the local API.
        
        Returns:
            Float value of current battery level (0-100%) or fallback value if request fails
        """
        try:
            response = requests.get(self.BATTERY_SOC_URL, timeout=self.API_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            # Extract battery level from 'percent' field
            battery_level = int(round(float(data['percent'])))
            logger.info(f"Successfully fetched battery level: {battery_level}%")
            return battery_level
        except (requests.exceptions.RequestException, ValueError, KeyError, TypeError) as e:
            logger.error(f"Failed to fetch battery level from API: {e}")
            return int(self.DEFAULT_BATTERY_LEVEL)

    def _fetch_battery_discharged(self, date):
        """
        Fetches the total battery discharged energy for a specific date from the local API.
        
        Args:
            date: Date string in format 'YYYY-MM-DD'
            
        Returns:
            Float value of total discharged energy in Wh or fallback value if request fails
        """
        try:
            response = requests.get(self.BATTERY_DISCHARGED_URL, params={'date': date}, timeout=self.API_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            # Extract total discharged from 'totalDischarged' field
            discharged = float(data['totalDischarged'])
            logger.info(f"Successfully fetched battery discharged: {discharged} Wh for {date}")
            return discharged
        except (requests.exceptions.RequestException, ValueError, KeyError, TypeError) as e:
            logger.error(f"Failed to fetch battery discharged from API: {e}")
            return self.DEFAULT_BATTERY_DISCHARGED

    def _fetch_battery_charged(self, date):
        """
        Fetches the total battery charged energy for a specific date from the local API.
        
        Args:
            date: Date string in format 'YYYY-MM-DD'
            
        Returns:
            Float value of total charged energy in Wh or fallback value if request fails
        """
        try:
            response = requests.get(self.BATTERY_CHARGED_URL, params={'date': date}, timeout=self.API_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            # Extract total charged from 'totalCharged' field
            charged = float(data['totalCharged'])
            logger.info(f"Successfully fetched battery charged: {charged} Wh for {date}")
            return charged
        except (requests.exceptions.RequestException, ValueError, KeyError, TypeError) as e:
            logger.error(f"Failed to fetch battery charged from API: {e}")
            return self.DEFAULT_BATTERY_CHARGED

    def _fetch_solar_production(self, date):
        """
        Fetches the total solar PV production for a specific date from the local API.
        Calculates actual PV power as: ac_out - battery_out + battery_in
        Returns 0 for negative values and sums all hourly values.
        
        Args:
            date: Date string in format 'YYYY-MM-DD'
            
        Returns:
            Float value of total solar PV production in Wh or fallback value if request fails
        """
        try:
            response = requests.get(self.SOLAR_AC_OUT_SUMMARY_URL, params={'date': date}, timeout=self.API_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            # Calculate PV power: ac_out - battery_out + battery_in for each hour, then sum
            total_pv = 0
            for item in data:
                if isinstance(item, dict):
                    ac_out = item.get('ac_out', 0)
                    battery_out = item.get('battery_out', 0)
                    battery_in = item.get('battery_in', 0)
                    pv_power = ac_out - battery_out + battery_in
                    # Add to total, using 0 if negative
                    total_pv += max(0, pv_power)
            
            logger.info(f"Successfully fetched solar PV production: {total_pv} Wh for {date}")
            return total_pv
        except (requests.exceptions.RequestException, ValueError, KeyError, TypeError) as e:
            logger.error(f"Failed to fetch solar PV production from API: {e}")
            return self.DEFAULT_SOLAR_PRODUCTION

    def _fetch_solar_current_power(self):
        """
        Fetches the current solar power (AC output) from the local API.
        
        Returns:
            Float value of current solar power in W or fallback value if request fails
        """
        try:
            response = requests.get(self.SOLAR_CURRENT_POWER_URL, timeout=self.API_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            # Extract current power from 'value' field
            current_power = float(data['value'])
            logger.info(f"Successfully fetched solar current power: {current_power} W")
            return current_power
        except (requests.exceptions.RequestException, ValueError, KeyError, TypeError) as e:
            logger.error(f"Failed to fetch solar current power from API: {e}")
            return self.DEFAULT_SOLAR_CURRENT

    def _fetch_grid_import(self, date):
        """
        Fetch grid import energy for a specific date from API.
        
        Args:
            date: Date string in format 'YYYY-MM-DD'
            
        Returns:
            Total imported energy in Watt-hours (as float)
        """
        try:
            response = requests.get(self.GRID_IMPORT_URL, params={'date': date}, timeout=self.API_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            imported = float(data['totalImported'])
            logger.info(f"Successfully fetched grid import: {imported} Wh for {date}")
            return imported
        except (requests.exceptions.RequestException, ValueError, KeyError, TypeError) as e:
            logger.error(f"Failed to fetch grid import from API: {e}")
            return self.DEFAULT_GRID_IMPORT

    def _fetch_grid_export(self, date):
        """
        Fetch grid export energy for a specific date from API.
        
        Args:
            date: Date string in format 'YYYY-MM-DD'
            
        Returns:
            Total exported energy in Watt-hours (as float)
        """
        try:
            response = requests.get(self.GRID_EXPORT_URL, params={'date': date}, timeout=self.API_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            exported = float(data['totalExported'])
            logger.info(f"Successfully fetched grid export: {exported} Wh for {date}")
            return exported
        except (requests.exceptions.RequestException, ValueError, KeyError, TypeError) as e:
            logger.error(f"Failed to fetch grid export from API: {e}")
            return self.DEFAULT_GRID_EXPORT

    def _fetch_solar_pv_chart_data(self, date):
        """
        Fetch solar PV power hourly data for chart display.
        Calculates actual PV power as: ac_out - battery_out + battery_in
        Returns 0 for negative values.
        
        Args:
            date: Date string in format 'YYYY-MM-DD'
            
        Returns:
            List of PV power values (in Wh) for 24 hours, or fallback data if request fails
        """
        try:
            response = requests.get(self.SOLAR_AC_OUT_SUMMARY_URL, params={'date': date}, timeout=self.API_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            # Calculate PV power: ac_out - battery_out + battery_in for each hour
            pv_values = []
            for item in data:
                if isinstance(item, dict):
                    ac_out = item.get('ac_out', 0)
                    battery_out = item.get('battery_out', 0)
                    battery_in = item.get('battery_in', 0)
                    pv_power = ac_out - battery_out + battery_in
                    # Return 0 if negative
                    pv_values.append(max(0, pv_power))
            
            logger.info(f"Successfully fetched PV chart data: {len(pv_values)} data points for {date}")
            return pv_values
        except (requests.exceptions.RequestException, ValueError, KeyError, TypeError) as e:
            logger.error(f"Failed to fetch PV chart data from API: {e}")
            # Fallback: return 24 hours of zero values
            return [0] * self.DEFAULT_CHART_HOURS
