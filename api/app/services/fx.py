import logging
import time
from decimal import Decimal
import httpx
import xml.etree.ElementTree as ET

from app.core.settings import settings

logger = logging.getLogger(__name__)

# Simple in-memory cache to avoid spamming TCMB
_fx_cache = {
    "rate": None,
    "timestamp": 0
}
CACHE_TTL_SECONDS = 3600  # 1 hour


def fetch_tcmb_usd_try() -> Decimal | None:
    """Fetches live USD/TRY rate from TCMB XML."""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get("https://www.tcmb.gov.tr/kurlar/today.xml")
            response.raise_for_status()

            tree = ET.fromstring(response.content)
            for currency in tree.findall("Currency"):
                if currency.get("CurrencyCode") == "USD":
                    selling_rate_str = currency.find("BanknoteSelling").text
                    if selling_rate_str:
                        return Decimal(selling_rate_str)

                    # If BanknoteSelling is empty, try ForexSelling
                    forex_rate_str = currency.find("ForexSelling").text
                    if forex_rate_str:
                        return Decimal(forex_rate_str)
        return None
    except Exception as e:
        logger.error(f"Error fetching TCMB rate: {e}")
        return None


def get_usd_try_rate() -> Decimal:
    """
    Fetches the current USD/TRY exchange rate.
    Uses TCMB if configured, else uses a mock fallback.
    """
    fallback_rate = Decimal("35.00")

    # Check if FX_PROVIDER is set to TCMB (case-insensitive)
    provider = getattr(settings, "FX_PROVIDER", "TCMB").upper()

    if provider == "TCMB":
        current_time = time.time()

        # Return cached rate if valid
        if _fx_cache["rate"] is not None and (current_time - _fx_cache["timestamp"] < CACHE_TTL_SECONDS):
            return _fx_cache["rate"]

        rate = fetch_tcmb_usd_try()
        if rate is not None and rate > 0:
            _fx_cache["rate"] = rate
            _fx_cache["timestamp"] = current_time
            logger.info(f"Updated live TCMB USD/TRY rate: {rate}")
            return rate

        logger.warning("Failed to fetch live TCMB rate. Using fallback.")
    else:
        logger.info(f"FX_PROVIDER is {provider}. Using fallback rate.")

    return fallback_rate


def convert_try_to_usd(amount_try: Decimal) -> Decimal:
    """Converts a TRY amount to USD using the current rate."""
    rate = get_usd_try_rate()
    if rate <= 0:
        raise ValueError("Invalid FX rate")

    amount_usd = amount_try / rate
    return Decimal(f"{amount_usd:.2f}")