# The schemas.py file defines the expected shape of data, both when receiving from the user and when returning data.
# Pydantic is a data validation and parsing library that works well with FastAPI. 

from pydantic import BaseModel
from datetime import date

# Schema for creating a new contact (used when users add a new contact)
class ContactCreate(BaseModel):
    name: str
    birthday: date

# Schema for returning a contact (used when we fetch data to return to users)
class Contact(ContactCreate):
    id: int
    user_id: int

    class Config:
        orm_mode = True
