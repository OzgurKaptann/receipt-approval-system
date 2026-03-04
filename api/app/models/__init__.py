# api/app/models/__init__.py
"""
Import all ORM models so they are registered on Base.metadata.
This fixes empty Base.metadata.tables and FK resolution issues.
"""

from app.models.user import User  # noqa: F401
from app.models.customer import Customer  # noqa: F401
from app.models.document import UploadedDocument  # noqa: F401
from app.models.deposit import Deposit  # noqa: F401
from app.models.audit_event import AuditEvent  # noqa: F401
from app.models.audit_event import AuditEvent
from app.models.document import UploadedDocument