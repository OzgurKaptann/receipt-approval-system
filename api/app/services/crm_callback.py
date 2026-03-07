import logging
import httpx
from decimal import Decimal
from dataclasses import dataclass
import uuid

from app.core.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class CRMCallbackResult:
    success: bool
    error: str | None = None


def notify_crm(
    document_id: uuid.UUID, 
    status: str, 
    final_amount_try: Decimal | None, 
    final_amount_usd: Decimal | None,
    mt_transaction_id: str | None = None
) -> CRMCallbackResult:
    """
    Notifies the CRM regarding the final status of a receipt approval workflow.
    """
    url = settings.CRM_WEBHOOK_URL
    if not url:
        logger.info(f"CRM_WEBHOOK_URL not set. Simulating MOCK CRM Callback for {document_id} -> {status}")
        return CRMCallbackResult(success=True)

    payload = {
        "document_id": str(document_id),
        "status": status,
        "amount_try": str(final_amount_try) if final_amount_try else None,
        "amount_usd": str(final_amount_usd) if final_amount_usd else None,
        "mt_transaction_id": mt_transaction_id
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            # Depending on CRM requirements, auth might be needed
            response = client.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"CRM notified successfully for document {document_id}")
            return CRMCallbackResult(success=True)
            
    except httpx.HTTPError as he:
        err_msg = f"HTTP error during CRM callback: {str(he)}"
        logger.error(err_msg)
        return CRMCallbackResult(success=False, error=err_msg)
    except Exception as e:
        err_msg = f"Generic error during CRM callback: {str(e)}"
        logger.error(err_msg)
        return CRMCallbackResult(success=False, error=err_msg)
