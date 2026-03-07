import logging
import httpx
from decimal import Decimal
from dataclasses import dataclass

from app.core.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class MTDepositResult:
    success: bool
    transaction_id: str | None
    error_message: str | None


def execute_deposit(mt_account_id: str, mt_currency: str, amount: Decimal) -> MTDepositResult:
    """
    Executes a deposit transaction to the Metatrader backend.
    """
    url = settings.CRM_MT_DEPOSIT_URL
    api_key = settings.CRM_MT_API_KEY

    if not url:
        logger.warning("CRM_MT_DEPOSIT_URL is not set. Executing MOCK deposit.")
        return MTDepositResult(
            success=True,
            transaction_id="MOCK_TX_12345",
            error_message=None
        )

    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "account_id": mt_account_id,
        "currency": mt_currency,
        "amount": str(amount),
        "type": "deposit"
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json=payload, headers=headers)
            
            if response.status_code in (200, 201):
                data = response.json()
                return MTDepositResult(
                    success=True,
                    transaction_id=data.get("transaction_id"),
                    error_message=None
                )
            else:
                logger.error(f"MT Deposit failed with status {response.status_code}: {response.text}")
                return MTDepositResult(
                    success=False,
                    transaction_id=None,
                    error_message=f"HTTP {response.status_code}: {response.text}"
                )
                
    except Exception as e:
        logger.error(f"MT Deposit network error: {e}")
        return MTDepositResult(
            success=False,
            transaction_id=None,
            error_message=str(e)
        )
