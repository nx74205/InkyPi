import requests
from datetime import datetime, timedelta
import pytz
import logging

logger = logging.getLogger(__name__)

class SolarBase:
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
        # Fetch price data from API
        price_data = self.fetch_price_data(bzn=bzn)
        
        if not price_data or not price_data.get('price') or not price_data.get('unix_seconds'):
            logger.warning("Could not fetch price data, using default values")
            return {
                "show": settings.get('showPriceData') == 'true',
                "icon": None,
                "currency_symbol": currency_symbol,
                "current_time": "N/A",
                "current_price": "N/A",
                "next_time": "N/A",
                "next_price": "N/A"
            }
        
        # Get CET timezone
        cet = pytz.timezone('Europe/Berlin')
        now = datetime.now(cet)
        
        # Find current and next price
        unix_seconds = price_data['unix_seconds']
        prices = price_data['price']
        
        current_price = None
        current_time = None
        next_price = None
        next_time = None
        
        # Find the closest time slot to now
        for i, timestamp in enumerate(unix_seconds):
            dt = datetime.fromtimestamp(timestamp, tz=cet)
            
            if dt <= now:
                current_price = prices[i]
                current_time = dt
            elif current_price is not None and next_price is None:
                next_price = prices[i]
                next_time = dt
                break
        
        # Fallback if we don't have current price (use first available)
        if current_price is None and len(prices) > 0:
            current_price = prices[0]
            current_time = datetime.fromtimestamp(unix_seconds[0], tz=cet)
            if len(prices) > 1:
                next_price = prices[1]
                next_time = datetime.fromtimestamp(unix_seconds[1], tz=cet)
        
        # Convert prices from Cent/kWh to Euro/kWh (divide by 100) and format with 3 decimal places
        current_price_euro = current_price / 100 if current_price is not None else None
        next_price_euro = next_price / 100 if next_price is not None else None
        
        # Format prices with decimal separator and 3 decimal places
        current_price_str = replace_decimals_func(f"{current_price_euro:.3f}") if current_price_euro is not None else "N/A"
        next_price_str = replace_decimals_func(f"{next_price_euro:.3f}") if next_price_euro is not None else "N/A"
        
        # Format times
        current_time_str = current_time.strftime("%H:%M") if current_time else "N/A"
        next_time_str = next_time.strftime("%H:%M") if next_time else "N/A"
        
        return {
            "show": settings.get('showPriceData') == 'true',
            "icon": None,  # Will be set by caller
            "currency_symbol": currency_symbol,
            "current_time": current_time_str,
            "current_price": f"{current_price_str} {currency_symbol}",
            "next_time": next_time_str,
            "next_price": f"{next_price_str} {currency_symbol}"
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
        # Fetch renewable share from API
        renewable_percentage = self.fetch_renewable_share_forecast(country=country)
        
        # Use fallback value if API call fails
        if renewable_percentage is None:
            logger.warning("Could not fetch renewable share, using fallback value")
            percentage_str = "N/A"
        else:
            # Format percentage with one decimal place
            percentage_formatted = f"{renewable_percentage:.1f}"
            
            # Apply decimal separator replacement if function provided
            if replace_decimals_func:
                percentage_formatted = replace_decimals_func(percentage_formatted)
            
            percentage_str = percentage_formatted + " %"
        
        return {
            "show": settings.get('dapCountry') == 'DE-LU',
            "icon": None,  # Will be set by caller
            "description": description,
            "percentage": percentage_str
        }

    def fetch_renewable_share_forecast(self, country="de"):
        """
        Fetches renewable share forecast from the Energy-Charts API.
        Returns the renewable share for the current timestamp.
        
        Args:
            country: Country code (default: "de" for Germany)
            
        Returns:
            Float value of current renewable share (0-100%) or None if request fails
        """
        base_url = "https://api.energy-charts.info/ren_share_forecast"
        
        params = {
            "country": country
        }
        
        try:
            logger.info(f"Fetching renewable share forecast from Energy-Charts API for {country}")
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Get current timestamp
            now = datetime.now().astimezone()
            current_unix = int(now.timestamp())
            
            # Find the renewable share for the current or closest past timestamp
            unix_seconds = data.get('unix_seconds', [])
            ren_share = data.get('ren_share', [])
            
            if not unix_seconds or not ren_share:
                logger.warning("No renewable share data available")
                return None
            
            # Find the closest timestamp that is <= current time
            current_share = None
            for i, timestamp in enumerate(unix_seconds):
                if timestamp <= current_unix:
                    if ren_share[i] is not None:
                        current_share = ren_share[i]
                else:
                    break
            
            if current_share is not None:
                logger.info(f"Current renewable share: {current_share:.1f}%")
                return current_share
            else:
                logger.warning("Could not find renewable share for current time")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Timeout while fetching renewable share forecast from Energy-Charts API")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching renewable share forecast from Energy-Charts API: {e}")
            return None
        except ValueError as e:
            logger.error(f"Error parsing JSON response from Energy-Charts API: {e}")
            return None

    def fetch_price_data(self, bzn="DE-LU", center_time=None):
        """
        Fetches day-ahead spot market price data from the Energy-Charts API.
        The function automatically fetches data for a 60-minute window (±30 minutes around center_time).
        Prices are converted from EUR/MWh to Cent/kWh.
        
        Args:
            bzn: Bidding zone (default: "DE-LU" for Germany/Luxembourg)
            center_time: Center datetime for the time window (default: current time in system timezone)
            
        Returns:
            Dictionary with price data:
            {
                "license_info": str,
                "unix_seconds": list[int],
                "price": list[float],  # in Cent/kWh
                "unit": str,  # "Cent / kWh"
                "deprecated": bool
            }
            Returns None if the request fails.
        """
        base_url = "https://api.energy-charts.info/price"
        
        # Use current time in local system timezone if no center_time is provided
        if center_time is None:
            # Get current time with system timezone
            center_time = datetime.now().astimezone()
        elif center_time.tzinfo is None:
            # If center_time has no timezone, assume it's in system timezone
            center_time = center_time.astimezone()
        
        # Calculate start and end times (±30 minutes)
        start_time = center_time - timedelta(minutes=30)
        end_time = center_time + timedelta(minutes=30)
        
        # Format as ISO 8601 with timezone
        start_str = start_time.strftime("%Y-%m-%dT%H:%M%z")
        end_str = end_time.strftime("%Y-%m-%dT%H:%M%z")
        
        # Format timezone offset correctly (add colon)
        start_str = start_str[:-2] + ':' + start_str[-2:]
        end_str = end_str[:-2] + ':' + end_str[-2:]
        
        params = {
            "bzn": bzn,
            "start": start_str,
            "end": end_str
        }
            
        try:
            logger.info(f"Fetching price data from Energy-Charts API for {bzn} ({start_str} to {end_str})")
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Convert prices from EUR/MWh to Cent/kWh
            # 1 EUR/MWh = 0.1 Cent/kWh (1 MWh = 1000 kWh, 1 EUR = 100 Cent)
            if data.get('price'):
                data['price'] = [round(p * 0.1, 2) if p is not None else None for p in data['price']]
                data['unit'] = 'Cent / kWh'
            
            logger.info(f"Successfully fetched price data: {len(data.get('price', []))} data points")
            return data
            
        except requests.exceptions.Timeout:
            logger.error("Timeout while fetching price data from Energy-Charts API")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching price data from Energy-Charts API: {e}")
            return None
        except ValueError as e:
            logger.error(f"Error parsing JSON response from Energy-Charts API: {e}")
            return None

