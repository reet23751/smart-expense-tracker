import json
from app.models.user import User


def test_user_password_hashing(app):
    with app.app_context():
        u = User(name="Test User", email="test@hash.com")
        u.set_password("mypassword")
        assert u.password_hash != "mypassword"
        assert u.check_password("mypassword") is True
        assert u.check_password("wrongpassword") is False


def test_user_registration_success(client, app):
    res = client.post("/api/auth/register", json={
        "name": "Sarah Connor",
        "email": "sarah@resistance.org",
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True

    with app.app_context():
        user = User.query.filter_by(email="sarah@resistance.org").first()
        assert user is not None
        assert user.name == "Sarah Connor"


def test_duplicate_email_registration_fails(client, user_a):
    res = client.post("/api/auth/register", json={
        "name": "Duplicate Alice",
        "email": "alice@test.com",  # Already exists in fixture
        "password": "Password123!",
        "confirm_password": "Password123!"
    })
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert any("already exists" in err.lower() for err in data["errors"])


def test_login_success_and_logout(client, user_a):
    # Login
    res = client.post("/api/auth/login", json={
        "email": "alice@test.com",
        "password": "SecurePass123!"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True

    # Logout
    res_logout = client.post("/api/auth/logout")
    assert res_logout.status_code == 200


def test_invalid_credentials_returns_401(client, user_a):
    res = client.post("/api/auth/login", json={
        "email": "alice@test.com",
        "password": "wrong-password"
    })
    assert res.status_code == 401
    data = res.get_json()
    assert data["success"] is False
