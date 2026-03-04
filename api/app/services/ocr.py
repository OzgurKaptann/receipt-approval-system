from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal


@dataclass(frozen=True)
class OcrResult:
    sender_name: str | None
    amount_try: Decimal | None
    transfer_date: datetime | None
    provider: str = "mock"


def parse_receipt_mock(*, file_path: str, original_file_name: str) -> OcrResult:
    """
    Demo OCR:
    filename format:
    Ali_Veli_1250.50_2026-03-04.jpg
    """

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

    if not sender_name:
        sender_name = "UNKNOWN SENDER"

    if amount_try is None:
        amount_try = Decimal("1000.00")

    if transfer_date is None:
        transfer_date = datetime.now(timezone.utc)

    return OcrResult(
        sender_name=sender_name,
        amount_try=amount_try,
        transfer_date=transfer_date,
    )