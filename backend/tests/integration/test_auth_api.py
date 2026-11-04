import pytest
from app.core.security import hash_password
from app.models.role import AppPermission, AppRole
from app.models.user import AppUser
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture
def seed_user(db_session: Session) -> AppUser:
    """Create a verified test user with ROLE_USER and CATALOG_READ."""
    perm = AppPermission(code="CATALOG_READ", name="Catalog Read", module="catalog")
    role = AppRole(code="ROLE_USER", name="User", permissions=[perm])
    user = AppUser(
        username="alice",
        email="alice@example.com",
        password_hash=hash_password("ValidPassword123!"),
        is_active=True,
        roles=[role],
    )
    db_session.add_all([perm, role, user])
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.mark.unit
def test_login_successful(client: TestClient, seed_user: AppUser) -> None:
    """Verify authenticating with correct credentials returns 200 and bearer token."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "ValidPassword123!"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "alice"
    assert "ROLE_USER" in data["user"]["roles"]
    assert "CATALOG_READ" in data["user"]["permissions"]


@pytest.mark.unit
def test_login_invalid_password_returns_generic_401(client: TestClient, seed_user: AppUser) -> None:
    """Verify invalid password returns generic constant-time 401 error."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "WrongPassword999!"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid username or password"


@pytest.mark.unit
def test_login_nonexistent_user_returns_generic_401(client: TestClient) -> None:
    """Verify non-existent user returns identical generic 401 error to prevent enumeration."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "nobody_exists", "password": "AnyPassword123!"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid username or password"


@pytest.mark.unit
def test_me_endpoint_requires_auth(client: TestClient) -> None:
    """Verify /auth/me rejects unauthenticated requests with HTTP 401."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.unit
def test_me_endpoint_with_valid_token(client: TestClient, seed_user: AppUser) -> None:
    """Verify /auth/me returns identity when authenticated."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "ValidPassword123!"},
    )
    token = login_resp.json()["access_token"]

    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


@pytest.mark.unit
def test_logout_revokes_token(client: TestClient, seed_user: AppUser) -> None:
    """Verify logout immediately invalidates token for subsequent requests."""
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "ValidPassword123!"},
    )
    token = login_resp.json()["access_token"]

    # Logout
    logout_resp = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logout_resp.status_code == 204

    # Subsequent request with revoked token must fail with 401
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 401
