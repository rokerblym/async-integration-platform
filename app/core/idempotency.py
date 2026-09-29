import hashlib, json

def payload_fingerprint(event_type: str, payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(f"{event_type}:{canonical}".encode()).hexdigest()
