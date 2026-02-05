# app/models/user.py

# from sqlalchemy import Integer, String
# from sqlalchemy.orm import Mapped, mapped_column

from fastapi_users.db import SQLAlchemyBaseUserTableUUID

from app.database.db import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"


# class User(Base):
#     __tablename__ = "users"

#     id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
#     name: Mapped[str] = mapped_column(String, index=True)
#     email: Mapped[str] = mapped_column(String, unique=True, index=True)

#     def __str__(self):
#         return f"({self.name}): {self.id}"
