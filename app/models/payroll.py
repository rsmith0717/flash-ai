# app/models/user.py
import enum

from sqlalchemy import Boolean, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


class PaySchedule(enum.Enum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


class SalaryType(enum.Enum):
    HOURLY = "hourly"
    SALARY = "salary"


class Payroll(Base):
    __tablename__ = "payroll"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id = mapped_column(ForeignKey("users.id"))
    pay_schedule: Mapped[PaySchedule] = mapped_column(
        Enum(PaySchedule, values_callable=lambda t: [str(item.value) for item in t]),
        default=PaySchedule.BIWEEKLY,
    )
    salary_type: Mapped[SalaryType] = mapped_column(
        Enum(SalaryType, values_callable=lambda t: [str(item.value) for item in t]),
        default=SalaryType.SALARY,
    )
    salary: Mapped[int] = mapped_column(Integer, index=True)
    terminated: Mapped[bool] = mapped_column(Boolean, default=False)
