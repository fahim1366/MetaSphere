from fastapi import APIRouter, Depends, Request, Response, Security, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, security_bearer
from app.models.user import AppUser
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    TokenResponse,
    UserRead,
)
from app.services.auth_service import (
    authenticate_user,
    change_user_password,
    logout_user,
)
from app.services.rbac_service import build_user_read

auth_router = APIRouter(prefix="/auth", tags=["Authentication & Session"])


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticate with username and password, returning an active session token.",
)
def login(
    login_req: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    return authenticate_user(
        db=db,
        username=login_req.username,
        password=login_req.password.get_secret_value(),
        client_ip=client_ip,
        user_agent=user_agent,
    )


@auth_router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="User Logout",
    description="Immediately invalidate active session token.",
)
def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(security_bearer),
    db: Session = Depends(get_db),
) -> Response:
    if credentials and credentials.credentials:
        client_ip = request.client.host if request.client else None
        logout_user(db=db, token=credentials.credentials, client_ip=client_ip)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@auth_router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile",
    description="Returns current authenticated user identity, roles, and effective permissions.",
)
def get_me(
    current_user: AppUser = Depends(get_current_user),
) -> UserRead:
    return build_user_read(current_user)


@auth_router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change Account Password",
    description="Updates user password and immediately invalidates all active sessions.",
)
def change_password(
    req: ChangePasswordRequest,
    request: Request,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    client_ip = request.client.host if request.client else None
    change_user_password(
        db=db,
        user=current_user,
        current_password=req.current_password.get_secret_value(),
        new_password=req.new_password.get_secret_value(),
        client_ip=client_ip,
    )
    return {"detail": "Password updated successfully; all active sessions have been invalidated"}
