# app/models/user.py

from sqlalchemy import Column, Integer, String, Boolean
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    profile_pic_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    hashed_password = Column(String, nullable=False)
