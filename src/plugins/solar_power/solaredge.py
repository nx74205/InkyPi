import requests
from datetime import datetime, timedelta
from plugins.solar_power.solar_provider import SolarProvider
from plugins.solar_power.dap_data_provider import DapDataProvider
import pytz
import logging

logger = logging.getLogger(__name__)

class Solaredge(SolarProvider):
    """
    SolarEdge API implementation for solar data retrieval.
    Requires SOLAREDGE_API_KEY and site_id in settings.
    
    API Documentation: https://knowledge-center.solaredge.com/sites/kc/files/se_monitoring_api.pdf
    """
    
    # Configuration constants
    SOLAREDGE_BASE_URL = 'https://monitoringapi.solaredge.com'
    API_TIMEOUT = 10
    CHART_VALUES_SHOWN = 14
    DEFAULT_CHART_HOURS = 24
    
    # Fallback values
    DEFAULT_BATTERY_LEVEL = 45
    DEFAULT_BATTERY_CHARGED = 2589.0
    DEFAULT_BATTERY_DISCHARGED = 1256.0
    DEFAULT_BATTERY_CAPACITY = 9700
    DEFAULT_SOLAR_MAX_POWER = 4400
    DEFAULT_SOLAR_PRODUCTION = 6820.0
    DEFAULT_SOLAR_CURRENT = 2300.0
    DEFAULT_CONSUMPTION = 0.0
    DEFAULT_FEEDIN = 0.0
    
    def __init__(self, api_key=None, site_id=None):
        """
        Initialize SolarEdge provider.
        
        Args:
            api_key: SolarEdge API key
            site_id: SolarEdge site ID
        """
        self.api_key = api_key
        self.site_id = site_id
        self.dap_provider = DapDataProvider()
        
        if not self.api_key or not self.site_id:
            logger.warning("SolarEdge API key or site_id not provided, using fallback values")
        
    def _get_today_str(self):
        """Returns today's date as string in YYYY-MM-DD format."""
        return datetime.now().strftime('%Y-%m-%d')
    
    def _wh_to_kwh(self, wh_value, decimals=1):
        """Convert Watt-hours to Kilowatt-hours with rounding."""
        return round(wh_value / 1000, decimals)
    
    def _make_api_request(self, endpoint, params=None):
        """
        Make a request to the SolarEdge API.
        
        Args:
            endpoint: API endpoint (e.g., 'currentPowerFlow')
            params: Additional query parameters
            
        Returns:
            JSON response data or None on error
        """
        if not self.api_key or not self.site_id:
            return None
            
        url = f"{self.SOLAREDGE_BASE_URL}/site/{self.site_id}/{endpoint}"
        
        request_params = {'api_key': self.api_key}
        if params:
            request_params.update(params)
        
        try:
            response = requests.get(url, params=request_params, timeout=self.API_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"SolarEdge API request failed for {endpoint}: {e}")
            return None
    
    def _fetch_current_power_flow(self):
        """
        Fetch current power flow data from SolarEdge API.
        
        Returns:
            Power flow data dict or None
        """
        data = self._make_api_request('currentPowerFlow')
        if data and 'siteCurrentPowerFlow' in data:
            return data['siteCurrentPowerFlow']
        return None
    
    def _fetch_energy_details(self, start_date, end_date, time_unit='HOUR'):
        """
        Fetch energy data for a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            time_unit: Time unit (DAY, QUARTER_OF_AN_HOUR, HOUR)
            
        Returns:
            Energy data dict or None
        """
        params = {
            'startDate': start_date,
            'endDate': end_date,
            'timeUnit': time_unit
        }
        return self._make_api_request('energy', params)
    
    def _fetch_energy_details_by_meter(self, start_date, end_date, time_unit='DAY', meters='Production'):
        """
        Fetch energy details data by meter type for a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            time_unit: Time unit (DAY, QUARTER_OF_AN_HOUR, HOUR)
            meters: Meter types (Production, Consumption, SelfConsumption, FeedIn, Purchased)
            
        Returns:
            Energy details data dict or None
        """
        # Calculate next day for end time
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        next_day = end_datetime.strftime('%Y-%m-%d')
        
        params = {
            'startTime': start_date + ' 00:00:00',
            'endTime': next_day + ' 00:00:00',
            'timeUnit': time_unit,
            'meters': meters
        }
        return self._make_api_request('energyDetails', params)
    
    def _fetch_storage_data(self, start_date, end_date):
        """
        Fetch battery storage data.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Storage data dict or None
        """
        # Calculate next day for end time
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        next_day = end_datetime.strftime('%Y-%m-%d')
        
        params = {
            'startTime': start_date + ' 00:15:00',
            'endTime': next_day + ' 00:00:01'
        }
        return self._make_api_request('storageData', params)
    
    def _fetch_hourly_storage_data(self, date):
        """
        Fetch hourly battery storage data for a specific date.
        
        Args:
            date: Date string in format 'YYYY-MM-DD'
            
        Returns:
            Dictionary with keys 'charged' and 'discharged', each containing a list of 24 hourly values in Wh
        """
        storage_data = self._fetch_storage_data(date, date)
        
        # Initialize arrays for 24 hours
        charged_hourly = [0] * 24
        discharged_hourly = [0] * 24
        
        if storage_data and 'storageData' in storage_data:
            batteries = storage_data['storageData'].get('batteries', [])
            
            for battery in batteries:
                telemetries = battery.get('telemetries', [])
                
                # Group telemetries by hour
                hourly_telemetries = {}
                for i in range(24):
                    hourly_telemetries[i] = []
                
                for telemetry in telemetries:
                    time_stamp = telemetry.get('timeStamp')
                    if time_stamp:
                        try:
                            # Parse timestamp (format: "2025-12-28 00:02:55")
                            dt = datetime.strptime(time_stamp, '%Y-%m-%d %H:%M:%S')
                            hour = dt.hour
                            
                            # Store telemetry with lifetime values
                            lifetime_charged = telemetry.get('lifeTimeEnergyCharged')
                            lifetime_discharged = telemetry.get('lifeTimeEnergyDischarged')
                            
                            if lifetime_charged is not None or lifetime_discharged is not None:
                                hourly_telemetries[hour].append({
                                    'charged': lifetime_charged,
                                    'discharged': lifetime_discharged
                                })
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Failed to parse timestamp {time_stamp}: {e}")
                            continue
                
                # Calculate hourly differences for each hour
                for hour in range(24):
                    telemetries_in_hour = hourly_telemetries[hour]
                    if len(telemetries_in_hour) >= 2:
                        # Get first and last telemetry in this hour
                        first = telemetries_in_hour[0]
                        last = telemetries_in_hour[-1]
                        
                        # Calculate charged difference
                        if first['charged'] is not None and last['charged'] is not None:
                            charged_diff = last['charged'] - first['charged']
                            charged_hourly[hour] += max(0, charged_diff)
                        
                        # Calculate discharged difference
                        if first['discharged'] is not None and last['discharged'] is not None:
                            discharged_diff = last['discharged'] - first['discharged']
                            discharged_hourly[hour] += max(0, discharged_diff)
        
        logger.info(f"Fetched hourly storage data for {date}: {len([c for c in charged_hourly if c > 0])} hours with charging")
        return {
            'charged': charged_hourly,
            'discharged': discharged_hourly
        }
    
    def _fetch_site_details(self):
        """
        Fetch site details including peak power.
        
        Returns:
            Site details dict or None
        """
        data = self._make_api_request('details')
        if data and 'details' in data:
            return data['details']
        return None
    
    def _fetch_power_details(self, start_date, end_date, meters='PURCHASED'):
        """
        Fetch power details data for a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            meters: Meter type (PURCHASED, PRODUCTION, SELFCONSUMPTION, FEEDIN)
            
        Returns:
            Power details data dict or None
        """
        # Calculate next day for end time
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        next_day = end_datetime.strftime('%Y-%m-%d')
        
        params = {
            'startTime': start_date + ' 00:15:00',
            'endTime': next_day + ' 00:00:01',
            'meters': meters
        }
        return self._make_api_request('powerDetails', params)
    
    def get_battery_data(self, replace_decimals_func):
        """
        Returns the battery dictionary.
        
        Args:
            replace_decimals_func: Function to replace decimal separator
            
        Returns:
            Dictionary containing battery data with icon, level, capacity, and current power
        """
        # Fetch current power flow for battery status
        power_flow = self._fetch_current_power_flow()
        
        # Fetch storage data for today
        today = self._get_today_str()
        storage_data = self._fetch_storage_data(today, today)
        
        # Extract battery level from power flow
        battery_level = self.DEFAULT_BATTERY_LEVEL
        if power_flow and 'STORAGE' in power_flow:
            battery_info = power_flow['STORAGE']
            if 'chargeLevel' in battery_info:
                battery_level = int(battery_info['chargeLevel'])
        
        # Extract charge/discharge from storage data
        battery_charged = self.DEFAULT_BATTERY_CHARGED
        battery_discharged = self.DEFAULT_BATTERY_DISCHARGED
        battery_capacity = self.DEFAULT_BATTERY_CAPACITY
        
        if storage_data and 'storageData' in storage_data:
            batteries = storage_data['storageData'].get('batteries', [])
            if batteries:
                # Get capacity from first telemetry entry if available
                first_battery = batteries[0]
                telemetries = first_battery.get('telemetries', [])
                if telemetries and len(telemetries) > 0:
                    first_telemetry = telemetries[0]
                    if 'fullPackEnergyAvailable' in first_telemetry:
                        battery_capacity = first_telemetry['fullPackEnergyAvailable']
                
                # Collect all lifeTimeEnergyCharged values to calculate today's charge
                lifetime_charged_values = []
                lifetime_discharged_values = []
                
                for battery in batteries:
                    telemetries = battery.get('telemetries', [])
                    for telemetry in telemetries:
                        # Collect lifetime energy values
                        if 'lifeTimeEnergyCharged' in telemetry and telemetry['lifeTimeEnergyCharged'] is not None:
                            lifetime_charged_values.append(telemetry['lifeTimeEnergyCharged'])
                        if 'lifeTimeEnergyDischarged' in telemetry and telemetry['lifeTimeEnergyDischarged'] is not None:
                            lifetime_discharged_values.append(telemetry['lifeTimeEnergyDischarged'])
                
                logger.info(f"Found {len(lifetime_charged_values)} charged values and {len(lifetime_discharged_values)} discharged values")
                
                # Calculate charged today as difference between first and last lifetime values
                if len(lifetime_charged_values) > 1:
                    battery_charged = lifetime_charged_values[-1] - lifetime_charged_values[0]
                else:
                    battery_charged = 0
                
                # Calculate discharged today as difference between first and last lifetime values
                if len(lifetime_discharged_values) > 1:
                    battery_discharged = lifetime_discharged_values[-1] - lifetime_discharged_values[0]
                else:
                    battery_discharged = 0
                                
                logger.info(f"battery_charged is {battery_charged} battery_discharged is {battery_discharged}")
        
        return {
            "icon": None,  # Will be set by caller
            "level": battery_level,
            "level_text": str(battery_level) + " %",
            "capacity": replace_decimals_func(str(self._wh_to_kwh(battery_capacity)) + " kWh"),
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
        # Fetch site details for max power
        site_details = self._fetch_site_details()
        solar_max_power = self.DEFAULT_SOLAR_MAX_POWER
        if site_details and 'peakPower' in site_details:
            # peakPower is in kW, convert to W
            solar_max_power = site_details['peakPower'] * 1000
        
        # Fetch energy details for today
        today = self._get_today_str()
        energy_data = self._fetch_energy_details_by_meter(today, today, time_unit='HOUR', meters='Production')
        
        solar_production_today = self.DEFAULT_SOLAR_PRODUCTION
        if energy_data and 'energyDetails' in energy_data:
            meters_data = energy_data['energyDetails'].get('meters', [])
            for meter in meters_data:
                if meter.get('type') == 'Production':
                    values = meter.get('values', [])
                    if values:
                        # Sum all energy values for today (in Wh)
                        solar_production_today = sum(v.get('value', 0) for v in values if v.get('value'))
                        break
        
        # Fetch current power from power flow
        
        power_flow = self._fetch_current_power_flow()
        solar_current_power = self.DEFAULT_SOLAR_CURRENT
        if power_flow and 'PV' in power_flow:
            pv_info = power_flow['PV']
            if 'currentPower' in pv_info:
                # currentPower is in kW
                solar_current_power = pv_info['currentPower'] * 1000

        logger.info("solar_current_power " + str(solar_current_power))
        return {
            "icon": None,  # Will be set by caller
            "max_power": replace_decimals_func(str(self._wh_to_kwh(solar_max_power))) + " kWp",
            "production_today": replace_decimals_func(str(self._wh_to_kwh(solar_production_today))) + " kWh",
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
        feedin_today = self.DEFAULT_FEEDIN
        
        # Fetch energy details from PURCHASED and FEEDIN meters using DAY time unit
        today = self._get_today_str()
        energy_data = self._fetch_energy_details_by_meter(today, today, time_unit='DAY', meters='Purchased,FeedIn')
        
        if energy_data and 'energyDetails' in energy_data:
            meters_data = energy_data['energyDetails'].get('meters', [])
            
            # Process all meters
            for meter in meters_data:
                if meter.get('type') == 'Purchased':
                    values = meter.get('values', [])
                    if values:
                        # Values are already in Wh (Wattstunden)
                        total_wh = sum(v.get('value', 0) for v in values if v.get('value'))
                        
                        if total_wh > 0:
                            consumption_today = total_wh

                elif meter.get('type') == 'FeedIn':
                    values = meter.get('values', [])
                    if values:
                        # Values are already in Wh (Wattstunden)
                        total_wh = sum(v.get('value', 0) for v in values if v.get('value'))
                        
                        if total_wh > 0:
                            feedin_today = total_wh

        logger.info("Import from Grid: " + str(consumption_today))
        logger.info("Export to Grid: " + str(feedin_today))

        return {
            "icon": None,  # Will be set by caller
            "consumption_today": replace_decimals_func(str(self._wh_to_kwh(consumption_today))) + " kWh",
            "production_today": replace_decimals_func(str(self._wh_to_kwh(feedin_today))) + " kWh",
            "grid_balance": replace_decimals_func(str(self._wh_to_kwh(consumption_today - feedin_today))) + " kWh"
        }

    def get_chart_data(self):
        """
        Returns the chart dictionary with hourly solar production for today.
        
        Returns:
            Dictionary containing chart data with max_value, values_shown, and data
        """
        today = self._get_today_str()
        
        # Fetch energy data with HOUR resolution
        energy_data = self._fetch_energy_details(today, today, time_unit='HOUR')
        
        # Fetch battery storage data
        storage_data = self._fetch_hourly_storage_data(today)
        charged_hourly = storage_data['charged']
        discharged_hourly = storage_data['discharged']
        
        chart_data = [0] * self.DEFAULT_CHART_HOURS
        
        if energy_data and 'energy' in energy_data:
            values = energy_data['energy'].get('values', [])
            
            # Calculate hourly values: value + charged - discharged
            hourly_data = [0] * 24
            for i, value_dict in enumerate(values):
                if i < 24:
                    value = value_dict.get('value', 0) or 0
                    charged = charged_hourly[i] if i < len(charged_hourly) else 0
                    discharged = discharged_hourly[i] if i < len(discharged_hourly) else 0
                    
                    # Calculate: value + charged - discharged
                    hourly_data[i] = value + charged - discharged
            
            chart_data = hourly_data
        
        # Get max power from site details
        site_details = self._fetch_site_details()
        max_value = self.DEFAULT_SOLAR_MAX_POWER
        if site_details and 'peakPower' in site_details:
            # peakPower is in kW, convert to W
            max_value = site_details['peakPower'] * 1000

        return {
            "max_value": max_value,
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
