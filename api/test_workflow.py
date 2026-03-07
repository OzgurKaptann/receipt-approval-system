import logging
import uuid
import time
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.settings import settings
from app.core.security import hash_password
from app.models.user import User
from app.models.customer import Customer
from app.models.document import UploadedDocument
from app.core.db import Base, get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = TestClient(app)

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_test_data():
    db = SessionLocal()
    # Create test user
    u = db.query(User).filter(User.email == "test@test.com").first()
    if not u:
        u = User(
            id=uuid.uuid4(),
            email="test@test.com",
            full_name="Test User",
            password_hash=hash_password("password"),
            is_active=True
        )
        db.add(u)
        db.commit()

    # Create test customer
    c = db.query(Customer).filter(Customer.crm_customer_id == "CUST123").first()
    if not c:
        c = Customer(
            id=uuid.uuid4(),
            user_id=u.id,
            crm_customer_id="CUST123",
            mt_account_id="MT12345",
            mt_currency="USD"
        )
        db.add(c)
        db.commit()

    return str(u.id), str(c.id)

def run_test():
    db = SessionLocal()
    u_id, c_id = setup_test_data()
    
    # Login
    response = client.post("/auth/login", json={"email": "test@test.com", "password": "password"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Upload Document
    import os
    random_bytes = os.urandom(32)
    files = {"file": ("test_Ali_Veli_1500_2026-03-05.jpg", random_bytes, "image/jpeg")}
    
    logger.info("Uploading document synchronously...")
    response = client.post(f"/documents/upload?customer_id={c_id}", files=files, headers=headers)
    assert response.status_code == 200
    doc_data = response.json()
    logger.info(f"Upload returned instantly! Status: {doc_data['status']}")
    
    doc_id = doc_data["id"]
    
    # Wait for celery to process OCR
    logger.info("Waiting for celery worker to process OCR...")
    for _ in range(15):
        time.sleep(1)
        db.expire_all()
        doc = db.query(UploadedDocument).filter(UploadedDocument.id == doc_id).first()
        if doc.status == "TG_PENDING":
            logger.info("Celery OCR Task completed successfully!")
            break
            
    assert doc.status == "TG_PENDING", f"Status didn't change, stayed at {doc.status}"
    
    public_key = doc.public_key
    
    # Simulate Telegram Approval
    logger.info("Simulating Telegram Approval...")
    tg_payload = {
        "callback_query": {
            "data": f"approve:{public_key}",
            "from": {"username": "tg_tester"}
        }
    }
    response = client.post("/telegram/webhook", json=tg_payload)
    assert response.status_code == 200
    
    # Wait for Telegram Celery Side-effect (should become SLACK_PENDING)
    for _ in range(15):
        time.sleep(1)
        db.expire_all()
        doc = db.query(UploadedDocument).filter(UploadedDocument.id == doc_id).first()
        if doc.status == "SLACK_PENDING":
            logger.info("Telegram -> Slack Celery transition completed!")
            break
            
    assert doc.status == "SLACK_PENDING", f"Status didn't change to SLACK_PENDING, stayed at {doc.status}"

    # Simulate Slack Approval
    logger.info("Simulating Slack Approval...")
    slack_payload = {
        "action": "approve",
        "public_key": public_key,
        "actor": {"id": "U12345", "username": "slack_tester"}
    }
    response = client.post("/slack/webhook", json=slack_payload)
    assert response.status_code == 200
    
    # Wait for Finalize Celery worker (should become APPROVED)
    logger.info("Waiting for Celery Finalize Worker (FX, MT, CRM)...")
    for _ in range(15):
        time.sleep(1)
        db.expire_all()
        doc = db.query(UploadedDocument).filter(UploadedDocument.id == doc_id).first()
        if doc.status == "APPROVED":
            logger.info("Celery Finalize Task completed successfully!")
            break
            
    assert doc.status == "APPROVED", f"Status didn't change to APPROVED, stayed at {doc.status}"
    
    # Verify Deposit creation
    from app.models.deposit import Deposit
    dep = db.query(Deposit).filter(Deposit.document_id == doc_id).first()
    assert dep is not None, "Deposit was not created by the finalize task!"
    assert dep.amount_usd is not None, "USD amount was not calculated!"
    
    logger.info(f"All terminal tests passed successfully! Final USD: {dep.amount_usd}")

if __name__ == "__main__":
    run_test()
