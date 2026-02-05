from app.exceptions.http_exceptions import (
    InvalidPayScheduleException,
    PayrollNotFoundException,
)
from fastapi import APIRouter, Depends
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.init_db import get_db
from app.schemas.payroll import PayrollCreate, PayrollPatch, PayrollRead
from app.services.payroll import (
    create_payroll,
    delete_payroll,
    get_payroll,
    update_salary,
)

router = APIRouter(prefix="/payroll", tags=["payroll"])


@router.post("/user/{user_id}", response_model=PayrollRead)
async def create_new_payroll(
    payroll: PayrollCreate, db: AsyncSession = Depends(get_db)
):
    try:
        if await get_payroll(db=db, user_id=payroll.user_id):
            raise Exception("Payroll already exsits")
        payroll_model = await create_payroll(db=db, payroll=payroll)
        return payroll_model
    except DBAPIError as e:
        print(e)
        if "invalid input value for enum" in str(e):
            raise InvalidPayScheduleException()
        else:
            raise


@router.get("/user/{user_id}", response_model=PayrollRead)
async def get_user_payroll(user_id: int, db: AsyncSession = Depends(get_db)):
    db_payroll = await get_payroll(db, user_id)
    if db_payroll is None:
        raise PayrollNotFoundException()
    return db_payroll


@router.delete("/user/{user_id}")
async def delete_existing_payroll(user_id: int, db: AsyncSession = Depends(get_db)):
    success = await delete_payroll(db, user_id)
    if not success:
        raise PayrollNotFoundException()
    return {"ok": True}


@router.put("/user/{user_id}/salary", response_model=PayrollRead)
async def update_user_salary(
    user_id: int, payroll: PayrollPatch, db: AsyncSession = Depends(get_db)
):
    updated = await update_salary(db=db, user_id=user_id, payroll=payroll)
    if updated is None:
        raise PayrollNotFoundException()
    return updated
