# from pydantic import BaseModel, EmailStr, Field
import uuid

from fastapi_users import schemas

# class UserBase(BaseModel):
#     name: str = Field(min_length=3)
#     email: EmailStr = Field(min_length=5)


# class UserCreate(UserBase):
#     pass  # In a real app you might add password or other fields here


# class UserRead(UserBase):
#     id: int = Field(gt=0)

#     class Config:
#         orm_mode = True


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass
