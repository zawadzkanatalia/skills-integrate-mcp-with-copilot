import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app import app


client = TestClient(app)


def test_login_and_protected_signup_flow():
    response = client.post(
        "/auth/login",
        json={"username": "teacher", "password": "password123"},
    )

    assert response.status_code == 200
    assert response.json()["authenticated"] is True

    signup_response = client.post(
        "/activities/Chess Club/signup?email=student@example.com"
    )
    assert signup_response.status_code == 200
    assert "student@example.com" in signup_response.json()["participants"]


def test_logout_clears_authentication():
    login_response = client.post(
        "/auth/login",
        json={"username": "teacher", "password": "password123"},
    )
    assert login_response.status_code == 200

    logout_response = client.post("/auth/logout")
    assert logout_response.status_code == 200

    me_response = client.get("/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["authenticated"] is False
