import hashlib, hmac

def verify_signature(secret: str, body: bytes, provided: str | None) -> bool:
    if not provided:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, provided)
