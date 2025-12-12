import logging

logger = logging.getLogger(__name__)


class SolarProvider:
    """
    Abstract base class for solar data providers.
    All methods raise NotImplementedError to indicate that they must be implemented by subclasses.
    """

    def get_battery_data(self, replace_decimals_func):
        """
        Returns the battery dictionary.
        
        Args:
            replace_decimals_func: Function to replace decimal separator
            
        Returns:
            Dictionary containing battery data with icon, level, capacity, and current power
            
        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("get_battery_data() is not implemented for this provider")

    def get_solar_data(self, replace_decimals_func):
        """
        Returns the solar dictionary.
        
        Args:
            replace_decimals_func: Function to replace decimal separator
            
        Returns:
            Dictionary containing solar data with icon, max_power, production_today, and current_power
            
        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("get_solar_data() is not implemented for this provider")

    def get_power_plant_data(self, replace_decimals_func):
        """
        Returns the power plant dictionary.
        
        Args:
            replace_decimals_func: Function to replace decimal separator
            
        Returns:
            Dictionary containing power plant data with icon and consumption_today
            
        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("get_power_plant_data() is not implemented for this provider")

    def get_chart_data(self):
        """
        Returns the chart dictionary.
        
        Returns:
            Dictionary containing chart data with max_value, values_shown, and data
            
        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("get_chart_data() is not implemented for this provider")

    def get_dap_data(self, settings, currency_symbol, replace_decimals_func, bzn="DE-LU"):
        """
        Returns the DAP (Day Ahead Price) dictionary.
        
        Args:
            settings: Plugin settings dictionary
            currency_symbol: Currency symbol (e.g., "€")
            replace_decimals_func: Function to replace decimal separator
            bzn: Bidding zone (default: "DE-LU" for Germany/Luxembourg)
            
        Returns:
            Dictionary containing DAP data with current and next price
            
        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("get_dap_data() is not implemented for this provider")

    def get_renewable_data(self, settings, replace_decimals_func=None, country="de", description="Anteil EEG"):
        """
        Returns the renewable energy data dictionary.
        
        Args:
            settings: Plugin settings dictionary
            replace_decimals_func: Function to replace decimal separator (optional)
            country: Country code (default: "de" for Germany)
            description: Description text (default: "Anteil EEG")
            
        Returns:
            Dictionary containing renewable energy data
            
        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("get_renewable_data() is not implemented for this provider")
