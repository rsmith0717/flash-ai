from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payroll import Payroll
from app.schemas.payroll import PayrollCreate, PayrollPatch


async def create_payroll(db: AsyncSession, payroll: PayrollCreate) -> Payroll:
    new_payroll = Payroll(
        user_id=payroll.user_id,
        pay_schedule=payroll.pay_schedule,
        salary_type=payroll.salary_type,
        salary=payroll.salary,
    )

    db.add(new_payroll)
    await db.flush()
    await db.commit()
    await db.refresh(new_payroll)
    return new_payroll


async def get_payroll(db: AsyncSession, user_id: int) -> Payroll | None:
    stmt = select(Payroll).where(Payroll.user_id == user_id)
    # session.query(Post).join(User).filter(User.id == 1).all()

    result = await db.execute(stmt)
    payroll = result.scalar_one_or_none()
    return payroll


async def update_salary(
    db: AsyncSession, user_id: int, payroll: PayrollPatch
) -> Payroll | None:
    db_payroll = await get_payroll(db, user_id)
    if not payroll:
        return None
    db_payroll.salary = payroll.salary
    await db.commit()
    db.refresh(db_payroll)
    return db_payroll


async def delete_payroll(db: AsyncSession, user_id: int) -> bool:
    payroll = await get_payroll(db, user_id)
    if not payroll:
        return False
    await db.delete(payroll)
    await db.commit()
    return True
