import boto3
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import logging

from app.core.settings import settings

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class OcrResult:
    sender_name: str | None
    amount_try: Decimal | None
    transfer_date: datetime | None
    raw_response: dict | None = None
    provider: str = "aws_textract"


def parse_receipt(file_path: str, original_file_name: str) -> OcrResult:
    """
    Analyzes the receipt using AWS Textract's analyze_expense API.
    If AWS Credentials are not set, it falls back to a mock data extractor.
    """
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        logger.warning("AWS Credentials not found. Falling back to Mock OCR.")
        return _mock_parse(file_path, original_file_name)

    textract = boto3.client(
        "textract",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION_NAME
    )

    try:
        # Check if file is on S3 or local
        if file_path.startswith("s3://"):
            bucket = file_path.split("/")[2]
            key = "/".join(file_path.split("/")[3:])
            response = textract.analyze_expense(
                Document={'S3Object': {'Bucket': bucket, 'Name': key}}
            )
        else:
            with open(file_path, "rb") as f:
                document_bytes = f.read()
            response = textract.analyze_expense(
                Document={'Bytes': document_bytes}
            )

        # Parse Expense Documents
        expense_docs = response.get("ExpenseDocuments", [])
        if not expense_docs:
            return OcrResult(None, None, None, raw_response=response)

        extracted_data = {"VENDOR_NAME": None, "TOTAL": None, "INVOICE_RECEIPT_DATE": None}
        
        for doc in expense_docs:
            for summary_field in doc.get("SummaryFields", []):
                field_type = summary_field.get("Type", {}).get("Text", "")
                if field_type in extracted_data:
                    val = summary_field.get("ValueDetection", {}).get("Text")
                    if val and not extracted_data[field_type]:
                        extracted_data[field_type] = val

        # Clean amount
        amount_val = extracted_data["TOTAL"]
        amount_try = None
        if amount_val:
            try:
                # Remove currency symbols and formatting
                cleaned_amount = ''.join(c for c in amount_val if c.isdigit() or c in '.,')
                cleaned_amount = cleaned_amount.replace(',', '.')
                amount_try = Decimal(cleaned_amount)
            except:
                pass

        # Clean date
        date_val = extracted_data["INVOICE_RECEIPT_DATE"]
        transfer_date = None
        if date_val:
            try:
                transfer_date = datetime.strptime(date_val, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except:
                pass

        return OcrResult(
            sender_name=extracted_data["VENDOR_NAME"],
            amount_try=amount_try,
            transfer_date=transfer_date,
            raw_response=response,
        )

    except Exception as e:
        logger.error(f"Textract analysis failed: {str(e)}")
        # In case of absolute failure, fallback to mock so flow doesn't die completely
        return _mock_parse(file_path, original_file_name)


def _mock_parse(file_path: str, original_file_name: str) -> OcrResult:
    """Mock parser when AWS Textract is unavailable."""
    base = original_file_name.rsplit(".", 1)[0]
    parts = base.split("_")

    sender_name = None
    amount_try = None
    transfer_date = None

    if len(parts) >= 2:
        sender_name = f"{parts[0]} {parts[1]}"

    if len(parts) >= 3:
        try:
            amount_try = Decimal(parts[2])
        except:
            amount_try = None

    if len(parts) >= 4:
        try:
            transfer_date = datetime.strptime(parts[3], "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
        except:
            transfer_date = None

    return OcrResult(
        sender_name=sender_name or "MOCK SENDER",
        amount_try=amount_try or Decimal("1000.00"),
        transfer_date=transfer_date or datetime.now(timezone.utc),
        raw_response={"mock": True, "original_name": original_file_name},
        provider="mock"
    )