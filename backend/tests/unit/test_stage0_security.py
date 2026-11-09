import uuid
from datetime import UTC, datetime, timedelta

import pytest
from app.core.password_policy import validate_password_strength
from app.core.permissions import ALL_PERMISSION_CODES, PERMISSION_DEFINITIONS
from app.core.security import hash_password, hash_session_token
from app.models.user import AppUser, AppUserSession
from app.schemas.user import UserCreate
from app.services.rbac_service import calculate_effective_permissions
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.orm import Session


@pytest.mark.unit
@pytest.mark.parametrize(
    "pwd",
    ["short1!A", "alllowercase123!", "ALLUPPERCASE123!", "NoDigitsHere!!", "NoSpecial12345"],
)
def test_password_policy_rejects_weak(pwd: str) -> None:
    with pytest.raises(ValueError):
        validate_password_strength(pwd)


@pytest.mark.unit
def test_password_policy_accepts_strong() -> None:
    assert validate_password_strength("Str0ng-Passw0rd!") == "Str0ng-Passw0rd!"


@pytest.mark.unit
def test_user_create_enforces_password_policy() -> None:
    with pytest.raises(ValidationError):
        UserCreate(username="bob", email="bob@example.com", password="weak")
    ok = UserCreate(username="bob", email="bob@example.com", password="Str0ng-Passw0rd!")
    assert ok.username == "bob"


@pytest.mark.unit
def test_permission_catalogue_is_consistent() -> None:
    codes = [d[0] for d in PERMISSION_DEFINITIONS]
    assert len(codes) == len(set(codes))
    assert {"SOURCE_MANAGE", "METADATA_EXTRACT"} <= set(ALL_PERMISSION_CODES)
    superuser = AppUser(id=uuid.uuid4(), username="root", email="r@x.io", password_hash="x")
    superuser.is_superuser = True
    assert calculate_effective_permissions(superuser) == list(ALL_PERMISSION_CODES)


def _login(client: TestClient, username: str, password: str) -> str:
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200
    return str(resp.json()["access_token"])


@pytest.fixture
def plain_user(db_session: Session) -> AppUser:
    user = AppUser(
        username="carol",
        email="carol@example.com",
        password_hash=hash_password("ValidPassword123!"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.mark.unit
def test_idle_session_is_rejected_and_revoked(
    client: TestClient, db_session: Session, plain_user: AppUser
) -> None:
    token = _login(client, "carol", "ValidPassword123!")
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200

    record = (
        db_session.query(AppUserSession)
        .filter_by(token_hash=hash_session_token(token))
        .one()
    )
    record.last_activity_at = datetime.now(UTC) - timedelta(hours=5)
    db_session.commit()

    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
    db_session.refresh(record)
    assert record.is_revoked is True


@pytest.mark.unit
def test_active_session_activity_is_refreshed(
    client: TestClient, db_session: Session, plain_user: AppUser
) -> None:
    token = _login(client, "carol", "ValidPassword123!")
    headers = {"Authorization": f"Bearer {token}"}
    record = (
        db_session.query(AppUserSession)
        .filter_by(token_hash=hash_session_token(token))
        .one()
    )
    stale = datetime.now(UTC) - timedelta(minutes=30)
    record.last_activity_at = stale
    db_session.commit()

    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    db_session.refresh(record)
    refreshed = record.last_activity_at
    if refreshed.tzinfo is None:
        refreshed = refreshed.replace(tzinfo=UTC)
    assert refreshed > stale + timedelta(minutes=10)


@pytest.mark.unit
def test_forbidden_response_does_not_leak_permission_names(
    client: TestClient, plain_user: AppUser
) -> None:
    token = _login(client, "carol", "ValidPassword123!")
    resp = client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Permission denied"
