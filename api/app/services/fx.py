from __future__ import annotations

import os
from decimal import Decimal, InvalidOperation


class FxConfigError(RuntimeError):
    """Raised when FX configuration in the environment is invalid."""


def get_try_to_usd_rate() -> Decimal:
    """
    Returns the TRY→USD FX rate as a Decimal quantized to 6 decimal places.

    Sprint-2 Step 2: only manual mode is supported.
    - FX_MODE: "manual" (default if unset)
    - FX_MANUAL_RATE: required when mode is manual, must be a positive decimal
    """
    mode = (os.getenv("FX_MODE") or "manual").strip().lower()

    if mode != "manual":
        raise FxConfigError(f"Unsupported FX_MODE={mode!r}; only 'manual' is supported.")

    raw_rate = os.getenv("FX_MANUAL_RATE")
    if not raw_rate:
        raise FxConfigError("FX_MANUAL_RATE is required when FX_MODE=manual.")

    try:
        rate = Decimal(raw_rate)
    except (InvalidOperation, TypeError):
        raise FxConfigError(f"FX_MANUAL_RATE={raw_rate!r} is not a valid decimal.") from None

    if rate <= 0:
        raise FxConfigError(f"FX_MANUAL_RATE must be positive, got {rate!r}.")

    return rate.quantize(Decimal("0.000001"))


if __name__ == "__main__":
    """
    Small self-check that can be run inside the container, e.g.:
      FX_MODE=manual FX_MANUAL_RATE=0.032 docker compose exec api python -m app.services.fx
    """
    try:
        rate = get_try_to_usd_rate()
        print(f"TRY->USD rate: {rate}")
    except FxConfigError as exc:
        print(f"FX config error: {exc}")

