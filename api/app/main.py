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


app = FastAPI(title="Receipt Approval System")

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
