from fastapi import FastAPI

import app.models  # noqa: F401
from app.routers.auth import router as auth_router
from app.routers.me import router as me_router
from app.routers.customers import router as customers_router
from app.routers.documents import router as documents_router
from app.routers.deposits import router as deposits_router
from app.routers.audit import router as audit_router
from app.routers.telegram import router as telegram_router
from app.routers.slack import router as slack_router


from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware

from app.core.rate_limit import limiter

app = FastAPI(title="Receipt Approval System")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(me_router)
app.include_router(customers_router)
app.include_router(documents_router)
app.include_router(deposits_router)
app.include_router(audit_router)
app.include_router(telegram_router)
app.include_router(slack_router)


@app.get("/health")
def health():
    return {"status": "ok"}
