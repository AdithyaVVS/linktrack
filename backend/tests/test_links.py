from datetime import datetime, timedelta, timezone

from app.models import Click, Link


def make_link(client, url="https://example.com", **extra):
    resp = client.post("/api/links", json={"original_url": url, **extra})
    assert resp.status_code == 201
    return resp.json()


# ---------- create ----------

def test_create_link(client):
    data = make_link(client, "https://www.wikipedia.org")
    assert len(data["short_code"]) == 7
    assert data["short_url"].endswith("/" + data["short_code"])
    assert data["is_active"] is True
    assert data["expires_at"] is None


def test_create_link_with_future_expiry(client):
    future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    data = make_link(client, expires_at=future)
    assert data["expires_at"] is not None


def test_create_rejects_invalid_url(client):
    resp = client.post("/api/links", json={"original_url": "not-a-url"})
    assert resp.status_code == 422


def test_create_rejects_javascript_scheme(client):
    resp = client.post("/api/links", json={"original_url": "javascript:alert(1)"})
    assert resp.status_code == 422


def test_create_rejects_past_expiry(client):
    resp = client.post(
        "/api/links",
        json={"original_url": "https://example.com", "expires_at": "2020-01-01T00:00:00Z"},
    )
    assert resp.status_code == 422


# ---------- collisions ----------

def test_collision_retries_with_new_code(client, monkeypatch):
    first = make_link(client)["short_code"]
    codes = iter([first, "uniq123"])  # first attempt collides, second succeeds
    monkeypatch.setattr("app.services.links.generate_short_code", lambda: next(codes))
    second = make_link(client)
    assert second["short_code"] == "uniq123"


def test_collision_gives_up_after_max_retries(client, monkeypatch):
    first = make_link(client)["short_code"]
    monkeypatch.setattr("app.services.links.generate_short_code", lambda: first)
    resp = client.post("/api/links", json={"original_url": "https://example.com"})
    assert resp.status_code == 503


# ---------- redirect ----------

def test_redirect_returns_302_and_records_click(client, db):
    data = make_link(client, "https://www.wikipedia.org")
    resp = client.get(f"/{data['short_code']}", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == data["original_url"]
    assert db.query(Click).count() == 1


def test_redirect_unknown_code_is_404(client):
    assert client.get("/doesnotexist", follow_redirects=False).status_code == 404


def test_redirect_expired_link_is_410(client, db):
    data = make_link(client)
    link = db.query(Link).filter_by(short_code=data["short_code"]).one()
    link.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.commit()
    resp = client.get(f"/{data['short_code']}", follow_redirects=False)
    assert resp.status_code == 410
    assert db.query(Click).count() == 0  # expired visits are not counted


def test_redirect_inactive_link_is_410(client, db):
    data = make_link(client)
    link = db.query(Link).filter_by(short_code=data["short_code"]).one()
    link.is_active = False
    db.commit()
    resp = client.get(f"/{data['short_code']}", follow_redirects=False)
    assert resp.status_code == 410


# ---------- list and stats ----------

def test_list_shows_click_counts(client):
    visited = make_link(client, "https://example.com/a")
    unvisited = make_link(client, "https://example.com/b")
    for _ in range(2):
        client.get(f"/{visited['short_code']}", follow_redirects=False)

    resp = client.get("/api/links")
    assert resp.status_code == 200
    counts = {item["short_code"]: item["click_count"] for item in resp.json()}
    assert counts[visited["short_code"]] == 2
    assert counts[unvisited["short_code"]] == 0


def test_stats_totals_and_daily_breakdown(client):
    data = make_link(client)
    for _ in range(3):
        client.get(f"/{data['short_code']}", follow_redirects=False)

    resp = client.get(f"/api/links/{data['short_code']}/stats")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["total_clicks"] == 3
    assert stats["last_clicked_at"] is not None
    assert len(stats["clicks_by_day"]) == 1
    assert stats["clicks_by_day"][0]["clicks"] == 3


def test_stats_for_unknown_code_is_404(client):
    assert client.get("/api/links/doesnotexist/stats").status_code == 404


# ---------- delete ----------

def test_delete_removes_link_and_its_clicks(client, db):
    data = make_link(client)
    client.get(f"/{data['short_code']}", follow_redirects=False)
    assert db.query(Click).count() == 1

    resp = client.delete(f"/api/links/{data['short_code']}")
    assert resp.status_code == 204

    db.expire_all()
    assert db.query(Click).count() == 0
    assert client.get(f"/{data['short_code']}", follow_redirects=False).status_code == 404


def test_delete_unknown_code_is_404(client):
    assert client.delete("/api/links/doesnotexist").status_code == 404
