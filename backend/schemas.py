"""Pydantic schemas describing the shape of data in/out of the API."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ContactCreate(BaseModel):
    name: str
    birth_month: int = Field(ge=1, le=12)
    birth_day: int = Field(ge=1, le=31)
    birth_year: Optional[int] = None


class Contact(ContactCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int


class UserBase(BaseModel):
    phone_number: str
    name: Optional[str] = None
    timezone: Optional[str] = None


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
