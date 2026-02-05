from pydantic import BaseModel, Field


class PayrollBase(BaseModel):
    user_id: int = Field(gt=0)


class PayrollCreate(PayrollBase):
    pay_schedule: str = Field()
    salary_type: str = Field()
    salary: int = Field()
    terminated: bool = Field(default=False)


class PayrollPatch(PayrollBase):
    salary: int = Field()
    terminated: bool = Field(default=False)


class PayrollRead(PayrollCreate):
    id: int = Field(gt=0)
