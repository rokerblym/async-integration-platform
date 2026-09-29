import hashlib, hmac
from app.core.signatures import verify_signature

def test_signature():
    secret = "abc"
    body = b'{"hello":"world"}'
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_signature(secret, body, sig)
    assert not verify_signature(secret, body, "bad")
