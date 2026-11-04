from fastapi import APIRouter

from app.api.routes.audit import audit_router
from app.api.routes.auth import auth_router
from app.api.routes.roles import roles_router
from app.api.routes.users import users_router

api_router = APIRouter()

# Mount authentication, users, roles, and audit routes
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(roles_router)
api_router.include_router(audit_router)
