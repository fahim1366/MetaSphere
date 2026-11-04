import pytest
from app.core.security import hash_password
from app.models.role import AppPermission, AppRole
from app.models.user import AppUser
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture
def auth_user(db_session: Session) -> AppUser:
    """Create a verified test user for session safety tests."""
    perm = AppPermission(code="CATALOG_READ", name="Catalog Read", module="catalog")
    role = AppRole(code="ROLE_USER", name="User", permissions=[perm])
    user = AppUser(
        username="bob",
        email="bob@example.com",
        password_hash=hash_password("InitialPassword123!"),
        is_active=True,
        roles=[role],
    )
    db_session.add_all([perm, role, user])
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.mark.unit
def test_password_change_invalidates_all_active_sessions(
    client: TestClient, auth_user: AppUser
) -> None:
    """Verify that updating account password instantly revokes all active session tokens."""
    # 1. Establish session 1
    login_1 = client.post(
        "/api/v1/auth/login",
        json={"username": "bob", "password": "InitialPassword123!"},
    )
    token_1 = login_1.json()["access_token"]

    # 2. Establish session 2
    login_2 = client.post(
        "/api/v1/auth/login",
        json={"username": "bob", "password": "InitialPassword123!"},
    )
    token_2 = login_2.json()["access_token"]

    # Verify both tokens are valid
    assert (
        client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_1}"}).status_code
        == 200
    )
    assert (
        client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_2}"}).status_code
        == 200
    )

    # 3. Change password using token 1
    change_resp = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token_1}"},
        json={
            "current_password": "InitialPassword123!",
            "new_password": "SuperSecretNewPassword999!",
        },
    )
    assert change_resp.status_code == 200

    # 4. Verify BOTH prior session tokens are immediately rejected with HTTP 401
    assert (
        client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_1}"}).status_code
        == 401
    )
    assert (
        client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_2}"}).status_code
        == 401
    )

    # 5. Verify new password can authenticate
    new_login = client.post(
        "/api/v1/auth/login",
        json={"username": "bob", "password": "SuperSecretNewPassword999!"},
    )
    assert new_login.status_code == 200
    new_token = new_login.json()["access_token"]
    assert (
        client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_token}"}).status_code
        == 200
    )
