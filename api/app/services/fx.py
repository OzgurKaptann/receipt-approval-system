import logging
from decimal import Decimal
import httpx

from app.core.settings import settings

logger = logging.getLogger(__name__)


def get_usd_try_rate() -> Decimal:
    """
    Fetches the current USD/TRY exchange rate.
    Uses a mock fallback if a real API (like TCMB or Fixer) is not configured or fails.
    """
    # USD -> TRY fallback rate
    fallback_rate = Decimal("35.00")
    
    try:
        # Example of calling a free public API for testing
        with httpx.Client(timeout=5.0) as client:
            response = client.get("https://api.exchangerate-api.com/v4/latest/USD")
            if response.status_code == 200:
                data = response.json()
                return Decimal(str(data["rates"]["TRY"]))
            
        logger.info("External FX API failed, using fallback FX rate.")
        return fallback_rate
    except Exception as e:
        logger.error(f"Failed to fetch real FX rate: {e}. Using fallback.")
        return fallback_rate


def convert_try_to_usd(amount_try: Decimal) -> Decimal:
    """Converts a TRY amount to USD using the current rate."""
    rate = get_usd_try_rate()
    if rate <= 0:
        raise ValueError("Invalid FX rate")
    
    amount_usd = amount_try / rate
    # Return formatted to 2 decimal places
    return Decimal(f"{amount_usd:.2f}")
