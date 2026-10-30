from app.limiter import limiter


def test_rejects_self_referencing_url(client):
    resp = client.post("/api/links", json={"original_url": "http://127.0.0.1:8000/abc"})
    assert resp.status_code == 422


def test_rejects_overlong_url(client):
    long_url = "https://example.com/" + "a" * 2100
    resp = client.post("/api/links", json={"original_url": long_url})
    assert resp.status_code == 422


def test_rate_limit_blocks_after_limit(client):
    limiter.enabled = True
    limiter.reset()
    try:
        statuses = [
            client.post("/api/links", json={"original_url": "https://example.com"}).status_code
            for _ in range(12)
        ]
    finally:
        limiter.enabled = False
        limiter.reset()
    assert statuses.count(201) == 10
    assert 429 in statuses
