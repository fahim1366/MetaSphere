import pytest
from app.core.permissions import PERMISSION_DEFINITIONS
from app.core.security import hash_password
from app.models.audit import AppSecurityAudit
from app.models.role import AppPermission, AppRole
from app.models.user import AppUser
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

STRONG = "Str0ng-Passw0rd!"


@pytest.fixture
def admin_headers(client: TestClient, db_session: Session) -> dict[str, str]:
    for code, name, module, desc in PERMISSION_DEFINITIONS:
        db_session.add(AppPermission(code=code, name=name, module=module, description=desc))
    db_session.add(AppRole(code="ROLE_USER", name="User", is_system=True))
    db_session.add(
        AppUser(
            username="root",
            email="root@example.com",
            password_hash=hash_password(STRONG),
            is_superuser=True,
        )
    )
    db_session.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "root", "password": STRONG})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _new_user(username: str = "dave", **over: object) -> dict[str, object]:
    body: dict[str, object] = {
        "username": username,
        "email": f"{username}@example.com",
        "password": STRONG,
        "role_codes": ["ROLE_USER"],
    }
    body.update(over)
    return body


@pytest.mark.unit
def test_create_user_ok_and_audited_atomically(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    resp = client.post("/api/v1/users", json=_new_user(), headers=admin_headers)
    assert resp.status_code == 201
    assert resp.json()["roles"] == ["ROLE_USER"]
    events = (
        db_session.execute(
            select(AppSecurityAudit).where(AppSecurityAudit.event_type == "USER_CREATED")
        )
        .scalars()
        .all()
    )
    assert len(events) == 1


@pytest.mark.unit
def test_create_user_rejects_unknown_role_and_persists_nothing(
    client: TestClient, db_session: Session, admin_headers: dict[str, str]
) -> None:
    resp = client.post(
        "/api/v1/users", json=_new_user("erin", role_codes=["NOPE"]), headers=admin_headers
    )
    assert resp.status_code == 400
    assert "NOPE" in resp.json()["detail"]
    assert db_session.execute(select(AppUser).where(AppUser.username == "erin")).first() is None


@pytest.mark.unit
def test_create_user_rejects_weak_password(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    resp = client.post(
        "/api/v1/users", json=_new_user("frank", password="weak"), headers=admin_headers
    )
    assert resp.status_code == 422


@pytest.mark.unit
def test_username_and_email_uniqueness_is_case_insensitive(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    assert (
        client.post("/api/v1/users", json=_new_user("grace"), headers=admin_headers).status_code
        == 201
    )
    dup_name = client.post(
        "/api/v1/users", json=_new_user("GRACE", email="other@example.com"), headers=admin_headers
    )
    assert dup_name.status_code == 400
    dup_mail = client.post(
        "/api/v1/users", json=_new_user("heidi", email="GRACE@example.com"), headers=admin_headers
    )
    assert dup_mail.status_code == 400


@pytest.mark.unit
def test_role_list_reports_counts_without_loading_users(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    client.post("/api/v1/users", json=_new_user("ivan"), headers=admin_headers)
    client.post("/api/v1/users", json=_new_user("judy"), headers=admin_headers)
    roles = client.get("/api/v1/roles", headers=admin_headers).json()
    role_user = next(r for r in roles if r["code"] == "ROLE_USER")
    assert role_user["assigned_user_count"] == 2


@pytest.mark.unit
def test_create_role_rejects_unknown_permission(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    resp = client.post(
        "/api/v1/roles",
        json={"code": "AUDITORS", "name": "Auditors", "permission_codes": ["AUDIT_READ", "BOGUS"]},
        headers=admin_headers,
    )
    assert resp.status_code == 400
    ok = client.post(
        "/api/v1/roles",
        json={"code": "AUDITORS", "name": "Auditors", "permission_codes": ["AUDIT_READ"]},
        headers=admin_headers,
    )
    assert ok.status_code == 201
    assert ok.json()["permissions"] == ["AUDIT_READ"]
