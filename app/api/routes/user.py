from fastapi import APIRouter, Depends

from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.user import auth_backend, current_active_user, fastapi_users

# from app.exceptions.http_exceptions import (
#     InvalidPayScheduleException,
#     PayrollNotFoundException,
# )

# from sqlalchemy.exc import DBAPIError
# from sqlalchemy.ext.asyncio import AsyncSession

# from app.database.init_db import get_db
# from app.schemas.payroll import PayrollCreate, PayrollPatch, PayrollRead
# from app.services.payroll import (
#     create_payroll,
#     delete_payroll,
#     get_payroll,
#     update_salary,
# )

router = APIRouter(prefix="/auth", tags=["auth"])


router.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/jwt", tags=["auth"]
)
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_reset_password_router(),
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_verify_router(UserRead),
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)


@router.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}
