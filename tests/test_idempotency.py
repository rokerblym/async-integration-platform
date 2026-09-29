from app.core.idempotency import payload_fingerprint

def test_fingerprint_stable():
    a = {"order_id": "1", "amount": 100, "status": "paid"}
    b = {"status": "paid", "amount": 100, "order_id": "1"}
    assert payload_fingerprint("order.updated", a) == payload_fingerprint("order.updated", b)

def test_fingerprint_changes():
    assert payload_fingerprint("x", {"a": 1}) != payload_fingerprint("x", {"a": 2})
