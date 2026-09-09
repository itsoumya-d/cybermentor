"""Smoke tests for the CyberMentor FastAPI backend.

Cover the challenge catalogue and validation paths. None of these call the
Anthropic API, so they run without credentials.
"""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _first_challenge_id():
    return client.get("/api/challenges").json()[0]["id"]


def test_health_reports_challenge_count():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["challenges"] > 0


def test_list_challenges():
    r = client.get("/api/challenges")
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_filter_challenges_by_difficulty():
    r = client.get("/api/challenges", params={"difficulty": "beginner"})
    assert r.status_code == 200


def test_challenge_detail_and_missing_challenge():
    challenge_id = _first_challenge_id()
    assert client.get(f"/api/challenges/{challenge_id}").status_code == 200
    assert client.get("/api/challenges/does-not-exist").status_code == 404


def test_hint_progression():
    challenge_id = _first_challenge_id()
    r = client.post(
        "/api/mentor/hint",
        json={"challenge_id": challenge_id, "hint_number": 0},
    )
    assert r.status_code == 200
    assert "hint" in r.json()


def test_explain_unknown_challenge_is_404():
    r = client.post("/api/mentor/explain", json={"challenge_id": "does-not-exist"})
    assert r.status_code == 404
