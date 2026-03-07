import os
import json
import time
import hmac
import hashlib
from fastapi.testclient import TestClient

from app.main import app
from app.core.settings import settings

client = TestClient(app)

def run_tests():
    # TEST 1: Telegram Invalid Secret
    print("Running TEST 1: Telegram Webhook without valid secret token")
    settings.TG_WEBHOOK_SECRET = "super_secret_token"
    res = client.post("/telegram/webhook", json={"callback_query": {"data": "approve:123"}})
    assert res.status_code == 401, f"Expected 401, got {res.status_code}"
    
    res2 = client.post("/telegram/webhook", json={"callback_query": {"data": "approve:123"}}, headers={"X-Telegram-Bot-Api-Secret-Token": "wrong_token"})
    assert res2.status_code == 401, f"Expected 401, got {res2.status_code}"
    print("Test 1 Passed.")

    # TEST 2: Slack Invalid Signature
    print("Running TEST 2: Slack Webhook without valid signature")
    settings.SLACK_SIGNING_SECRET = "test_slack_secret"
    payload = {"action": "approve", "public_key": "123", "actor": {"id": "1", "username": "a"}}
    
    # Send without signature
    res3 = client.post("/slack/webhook", json=payload)
    assert res3.status_code == 401, f"Expected 401 for no signature, got {res3.status_code}"

    # Send with invalid signature
    timestamp = str(int(time.time()))
    res4 = client.post("/slack/webhook", json=payload, headers={"X-Slack-Signature": "v0=invalid", "X-Slack-Request-Timestamp": timestamp})
    assert res4.status_code == 401, f"Expected 401 for invalid signature, got {res4.status_code}"
    print("Test 2 Passed.")

    # TEST 3: Valid Slack Signature
    print("Running TEST 3: Slack Webhook WITH valid signature")
    timestamp_valid = str(int(time.time()))
    body_str = json.dumps(payload, separators=(',', ':'))
    sig_basestring = f"v0:{timestamp_valid}:{body_str}"
    valid_signature = "v0=" + hmac.new(
        settings.SLACK_SIGNING_SECRET.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Needs valid DB record so it won't 400 immediately, but since we are just checking if it gets past 401 signature auth:
    # We will accept a 400 (document not found) or 200, but NOT 401
    res5 = client.post("/slack/webhook", content=body_str, headers={"X-Slack-Signature": valid_signature, "X-Slack-Request-Timestamp": timestamp_valid, "Content-Type": "application/json"})
    assert res5.status_code != 401, f"Valid signature was rejected with 401! Got: {res5.status_code}"
    print("Test 3 Passed.")

    # TEST 4: Rate Limiting
    client.app.state.limiter.reset() # clear memory limits if any
    
    import uuid
    u_id = str(uuid.uuid4())
    print("Running TEST 4: Rate limiter on /upload")
    headers = {"Authorization": "Bearer fake_token"}
    files = {"file": ("test.jpg", b"fake", "image/jpeg")}
    
    # Using raw TestClient bypasses auth context sometimes, so we mock user dependencies 
    from app.core.auth import get_current_user
    from app.models.user import User
    from app.models.customer import Customer
    from app.core.security import hash_password
    from app.core.db import SessionLocal
    
    db = SessionLocal()
    u = db.query(User).filter(User.email == "test@test.com").first()
    if not u:
        u = User(id=uuid.uuid4(), email="test@test.com", full_name="Test User", password_hash=hash_password("password"), is_active=True)
        db.add(u)
        db.commit()

    c = db.query(Customer).filter(Customer.crm_customer_id == "CUST123").first()
    if not c:
        c = Customer(id=uuid.uuid4(), user_id=u.id, crm_customer_id="CUST123", mt_account_id="MT12345", mt_currency="USD")
        db.add(c)
        db.commit()
    
    app.dependency_overrides[get_current_user] = lambda: u

    success_count = 0
    fail_count = 0
    for i in range(7):
        # file parsing must be re-opened or reset per request
        files = {"file": ("test.jpg", b"fake", "image/jpeg")}
        res6 = client.post(f"/documents/upload?customer_id={c.id}", files=files)
        if res6.status_code == 429:
            fail_count += 1
        elif res6.status_code in (200, 409):
            success_count += 1

    app.dependency_overrides.clear()
    
    assert fail_count > 0, "Rate limiter did not block excessive requests!"
    print(f"Test 4 Passed. (Blocked {fail_count} excess requests)")

    print("ALL SECURITY TESTS PASSED SUCESSFULLY.")

if __name__ == "__main__":
    run_tests()
